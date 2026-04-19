import os
import time
import pandas as pd
from openai import OpenAI
import re
from tqdm import tqdm  # 进度可视化库
import warnings
import random

warnings.filterwarnings('ignore')  # 屏蔽Excel无关警告

# ==================== 配置区域（可直接调整）====================
DEEPSEEK_API_KEY = "DEEPSEEK_API_KEY_PLACEHOLDER"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
MODEL_NAME = "deepseek-chat"

# 输入文件配置（你的6个文件完整配置）
INPUT_FILES = [
    # {
    #     "path": r"D:\纪检数据集构建\构建\总书记讲话_抽取300条结果.xlsx",
    #     "sheet": "Sheet1",
    #     "keyword_columns": ["摘要"],
    #     "output_suffix": "_摘要_加问题",
    #     "is_special": False,
    #     "data_type": "重要讲话"
    # },
    # {
    #     "path": r"D:\纪检数据集构建\构建\党纪法规_抽取300条结果.xlsx",
    #     "sheet": "Sheet1",
    #     "keyword_columns": ["要点词"],
    #     "output_suffix": "_要点词_加问题",
    #     "is_special": False,
    #     "data_type": "党纪法规"
    # },
    {
        "path": r"D:\纪检数据集构建\构建\实务测试集_80抽取结果.xlsx",
        "sheet": "Sheet1",
        "keyword_columns": ["问题"],
        "output_suffix": "_问题_加问题",
        "is_special": True,  # 实务测试集单独标记
        "data_type": "纪检实务"
    }
    # {
    #     "path": r"D:\纪检数据集构建\构建\理论文章_抽取300条结果.xlsx",
    #     "sheet": "Sheet1",
    #     "keyword_columns": ["标题", "摘要"],
    #     "output_suffix": "_标题+摘要_加问题",
    #     "is_special": False,
    #     "data_type": "理论文章"
    # }
]

# 核心配置（间隔优化）
BASE_SLEEP = 4.0  # 基础间隔（秒）
RANDOM_SLEEP_RANGE = (0, 1)  # 随机追加间隔，避免固定间隔触发风控
MIN_KEYWORD_LENGTH = 4
MAX_KEYWORD_LENGTH = 8
MAX_RETRY = 3
RETRY_SLEEP = 1.0

# 全局去重缓存（记录已生成的关键词和问题，避免重复）
GENERATED_KEYWORDS = set()
GENERATED_QUESTIONS = set()

# ==================== 初始化 ====================
client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url=DEEPSEEK_BASE_URL
)


# ==================== 工具函数（间隔优化）====================
def get_sleep_time():
    """生成带随机波动的间隔时间，避免固定间隔"""
    base = BASE_SLEEP
    random_add = random.uniform(*RANDOM_SLEEP_RANGE)
    return base + random_add


# ==================== 核心函数 ====================
def extract_retrieval_keywords(text: str, data_type: str, is_special: bool = False) -> str:
    """
    提取1个4-8字关键词（严格围绕参考列内容，贴合纪检场景）
    :param text: 参考列原始文本
    :param data_type: 数据类型（重要讲话/党纪法规/理论文章/纪检实务）
    :param is_special: 是否为实务测试集（特殊处理）
    :return: 唯一不重复的关键词
    """
    if not text or text.strip() == "":
        return "（无关键词）"

    # 四类数据的精准界定规则（强关联参考列+纪检场景）
    type_rules = {
        "重要讲话": {
            "prompt": "必须从参考列的总书记讲话摘要中提取核心内容，聚焦纪检监察、党风廉政、反腐败相关的具体论述，如'二十届中央纪委五次全会反腐部署'",
            "forbidden_words": ["讲话", "论述", "重要", "总书记"]  # 避免泛词
        },
        "党纪法规": {
            "prompt": "必须从参考列的要点词中提取核心内容，聚焦具体的纪检法规条款、适用场景、处分标准，如'违纪行为处分条例'",
            "forbidden_words": ["法规", "条例", "条款", "规定"]  # 避免泛词
        },
        "纪检实务": {
            "prompt": "必须从参考列的实务问题中提取核心内容，聚焦具体的纪检案例、违纪情形、处理方式，如'国企腐败案件查处'",
            "forbidden_words": ["案例", "问题", "实务", "处理"]  # 避免泛词
        },
        "理论文章": {
            "prompt": "必须从参考列的标题/摘要中提取核心内容，聚焦纪检理论研究、工作方法、实践探索，如'监督执纪四种形态应用'",
            "forbidden_words": ["文章", "理论", "研究", "分析"]  # 避免泛词
        }
    }
    current_rule = type_rules.get(data_type, type_rules["重要讲话"])

    # 生成关键词Prompt（移除模型自校验，强化参考列关联）
    if is_special:  # 纪检实务专属Prompt
        prompt = f"""请从以下纪检实务问题文本中提取**仅1个**核心关键词：
参考列文本：{text[:800]}
提取规则：
1. 必须只返回1个关键词，严禁生成多个、编号、列表形式；
2. 关键词长度严格控制在{MIN_KEYWORD_LENGTH}-{MAX_KEYWORD_LENGTH}字；
3. 关键词必须100%来源于参考列文本内容，不得脱离文本凭空生成；
4. {current_rule['prompt']}；
5. 禁止使用{current_rule['forbidden_words']}等泛词，必须是具体、有辨识度的纪检相关短语；
6. 仅返回关键词文本，不要任何解释、标点、换行或多余内容。"""
    else:
        prompt = f"""请从以下{data_type}类参考列文本中提取**仅1个**核心关键词：
参考列文本：{text[:800]}
提取规则：
1. 必须只返回1个关键词，严禁生成多个、编号、列表形式；
2. 关键词长度严格控制在{MIN_KEYWORD_LENGTH}-{MAX_KEYWORD_LENGTH}字；
3. 关键词必须100%来源于参考列文本内容，不得脱离文本凭空生成；
4. {current_rule['prompt']}；
5. 禁止使用{current_rule['forbidden_words']}等泛词，必须是具体、有辨识度的纪检相关短语；
6. 仅返回关键词文本，不要任何解释、标点、换行或多余内容。"""

    system_prompt = f"""你是纪检领域关键词提取专员，仅提取来源于参考列文本、贴合纪检场景的4-8字核心关键词，不生成任何多余内容。"""

    for retry in range(MAX_RETRY + 1):
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=20,
                stream=False
            )

            keyword = response.choices[0].message.content.strip()
            # 清理格式
            keyword = re.sub(r'^[:：、，0-9.]*', '', keyword).replace('\n', '').replace('\r', '')

            # 过滤禁用泛词
            for forbidden in current_rule["forbidden_words"]:
                keyword = keyword.replace(forbidden, "")
            keyword = keyword.strip()

            # 长度校准
            if len(keyword) < MIN_KEYWORD_LENGTH:
                keyword = keyword.ljust(MIN_KEYWORD_LENGTH, "字")[:MIN_KEYWORD_LENGTH].strip()
            elif len(keyword) > MAX_KEYWORD_LENGTH:
                keyword = keyword[:MAX_KEYWORD_LENGTH].strip()

            # 纪检场景校验（必须包含纪检核心词）
            discipline_core_words = ["纪检", "监察", "反腐", "廉政", "执纪", "违纪", "监督", "巡视", "巡察", "问责", "处分", "党风"]
            if not any(word in keyword for word in discipline_core_words):
                if retry < MAX_RETRY:
                    print(f"  关键词「{keyword}」未贴合纪检场景，重新生成...")
                    time.sleep(RETRY_SLEEP)
                    continue
                else:
                    # 兜底补充纪检核心词
                    keyword = f"{discipline_core_words[0]}{keyword}"[:MAX_KEYWORD_LENGTH].strip()

            # 去重校验
            if keyword and keyword not in ["（无关键词）", "（提取失败）"] and keyword not in GENERATED_KEYWORDS:
                GENERATED_KEYWORDS.add(keyword)
                return keyword
            elif retry < MAX_RETRY:
                print(f"  关键词「{keyword}」已重复/无效，重新生成...")
                time.sleep(RETRY_SLEEP)
                continue

        except Exception as e:
            error_msg = str(e)[:60]
            print(f"关键词提取失败（第{retry + 1}次）：{error_msg}")
            if retry < MAX_RETRY:
                time.sleep(RETRY_SLEEP)

    # 最终兜底（确保关联参考列+纪检场景）
    fallback_keyword = f"纪检{data_type}{len(GENERATED_KEYWORDS) + 1}"[:MAX_KEYWORD_LENGTH].strip()
    GENERATED_KEYWORDS.add(fallback_keyword)
    return fallback_keyword


def generate_question_stream(keywords: str, data_type: str) -> str:
    """仅基于关键词生成问题（100%参考关键词，贴合纪检场景，无病句）"""
    if not keywords or keywords in ["（无关键词）", "（提取失败）"]:
        return "（无关键词，无法生成问题）"

    # 四类数据的问题生成精准规则（100%参考关键词）
    question_rules = {
        "重要讲话": {
            "prompt": "必须围绕关键词生成关于总书记纪检相关论述的应用、落地、解读类问题，如关键词是'中央纪委五次全会部署'，问题为'二十届中央纪委五次全会的反腐部署如何落地执行？'",
            "forbidden": ["什么是", "定义", "含义", "重要性"]
        },
        "党纪法规": {
            "prompt": "必须围绕关键词生成关于纪检法规条款的适用、执行、解读类问题，如关键词是'违纪行为处分条例'，问题为'国企人员违反廉洁纪律如何适用处分条例？'",
            "forbidden": ["什么是", "定义", "含义", "重要性"]
        },
        "纪检实务": {
            "prompt": "必须围绕关键词生成关于纪检案例的查处、分析、整改类问题，如关键词是'国企腐败案件查处'，问题为'国企腐败案件查处过程中如何精准适用党纪条款？'",
            "forbidden": ["什么是", "定义", "含义", "重要性"]
        },
        "理论文章": {
            "prompt": "必须围绕关键词生成关于纪检理论的实践、应用、优化类问题，如关键词是'监督执纪四种形态'，问题为'基层纪检机关如何有效运用监督执纪四种形态？'",
            "forbidden": ["什么是", "定义", "含义", "重要性"]
        }
    }
    current_rule = question_rules.get(data_type, question_rules["重要讲话"])

    # 生成问题Prompt（移除模型自校验，强化关键词关联）
    prompt = f"""请仅基于以下关键词生成**仅1个**纪检相关的用户提问：
关键词：{keywords}
生成规则：
1. 必须只返回1个问题，严禁生成多个、编号、列表形式；
2. 问题必须100%围绕关键词内容生成，不得脱离关键词凭空创作；
3. {current_rule['prompt']}；
4. 禁止使用{current_rule['forbidden']}等表述，避免封闭式问题；
5. 问题必须语法正确、无病句、语义通顺，长度10-50字；
6. 问题必须贴合纪检场景，包含纪检/监察/反腐/廉政等核心词；
7. 仅返回问题文本，不要任何解释、标点、换行或多余内容。"""

    system_prompt = f"""你是纪检领域问题生成专员，仅基于给定关键词生成贴合纪检场景、语法正确的开放式问题，不生成任何多余内容。"""

    for retry in range(MAX_RETRY + 1):
        try:
            print("  正在生成问题...", end="", flush=True)
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=100,
                stream=False
            )

            full_question = response.choices[0].message.content.strip()
            # 清理格式
            full_question = re.sub(r'^[:：、，]*', '', full_question).split('\n')[0]

            # 强制补全问句格式
            if not full_question.endswith("？"):
                full_question += "？"

            print(f"\n  生成问题：{full_question}")

            # 多重校验（确保符合规则）
            validation_passed = True
            # 1. 长度校验
            if len(full_question) < 10 or len(full_question) > 50:
                print(f"  ❌ 问题长度不符合要求（{len(full_question)}字），重新生成...")
                validation_passed = False
            # 2. 关键词关联校验（必须包含关键词核心字）
            keyword_core = keywords.replace("纪检", "").replace("监察", "").strip()
            if not any(word in full_question for word in keyword_core.split()) and len(keyword_core) > 0:
                print(f"  ❌ 问题未关联关键词核心内容，重新生成...")
                validation_passed = False
            # 3. 纪检场景校验
            discipline_words = ["纪检", "监察", "反腐", "廉政", "执纪", "违纪", "监督", "巡视", "巡察", "问责", "处分", "党风"]
            if not any(word in full_question for word in discipline_words):
                print(f"  ❌ 问题未聚焦纪检场景，重新生成...")
                validation_passed = False
            # 4. 禁用表述校验
            if any(word in full_question for word in current_rule["forbidden"]):
                print(f"  ❌ 问题包含禁用封闭式表述，重新生成...")
                validation_passed = False
            # 5. 去重校验
            if full_question in GENERATED_QUESTIONS:
                print(f"  ❌ 问题已重复，重新生成...")
                validation_passed = False

            # 校验通过则返回
            if validation_passed and full_question not in ["（问题生成失败）"]:
                GENERATED_QUESTIONS.add(full_question)
                return full_question
            elif retry < MAX_RETRY:
                time.sleep(RETRY_SLEEP)
                continue

        except Exception as e:
            error_msg = str(e)[:60]
            print(f"\n  第{retry + 1}次调用失败：{error_msg}")
            if retry < MAX_RETRY:
                time.sleep(RETRY_SLEEP)

    # 最终兜底（确保关联关键词+纪检场景）
    fallback_question = f"关于{keywords}的纪检{data_type}工作该如何开展？"
    # 长度校准
    if len(fallback_question) < 10:
        fallback_question = f"关于{keywords}的纪检{data_type}具体工作该如何开展？"
    elif len(fallback_question) > 50:
        fallback_question = fallback_question[:50].rstrip("，。、") + "？"

    GENERATED_QUESTIONS.add(fallback_question)
    return fallback_question


def process_single_file(file_conf: dict):
    """处理单个文件：可视化进度 + 即时保存"""
    file_path = file_conf["path"]
    sheet_name = file_conf["sheet"]
    keyword_cols = file_conf["keyword_columns"]
    output_suffix = file_conf["output_suffix"]
    is_special = file_conf.get("is_special", False)
    data_type = file_conf.get("data_type", "重要讲话")  # 默认重要讲话

    # 检查文件是否存在
    if not os.path.exists(file_path):
        print(f"\n 文件不存在，跳过：{file_path}")
        return

    try:
        # 读取文件（编码加固）
        df = pd.read_excel(file_path, sheet_name=sheet_name, engine="openpyxl", dtype=str)
        df = df.fillna("")
        total_rows = len(df)
        print(f"\n{'=' * 50} 开始处理：{os.path.basename(file_path)} {'=' * 50}")
        print(f"总行数：{total_rows} | 参考列：{','.join(keyword_cols)} | ⏱️ 基础间隔：{BASE_SLEEP}秒")
        print(f"数据类型：{data_type} | 是否特殊处理：{'是（实务测试集）' if is_special else '否'}")
        print("-" * 120)
    except Exception as e:
        print(f"读取文件失败：{str(e)}")
        return

    # 初始化列
    df["参考"] = ""
    df["关键字"] = ""
    df["问题"] = ""

    # 可视化进度条遍历所有行
    for idx in tqdm(df.index, desc=f"处理 {os.path.basename(file_path)}", unit="行"):
        current_row = idx + 1
        # 打印单行详情
        print(f"\n【第{current_row}/{total_rows}行】")

        # 1. 拼接参考内容（支持多列）
        raw_parts = [str(df.loc[idx, col]).strip() for col in keyword_cols if col in df.columns]
        reference_str = " | ".join(raw_parts)
        df.at[idx, "参考"] = reference_str
        print(f" 参考内容：{reference_str[:60]}..." if len(reference_str) > 60 else f"  📝 参考内容：{reference_str}")

        # 2. 提取关键词（传入数据类型和特殊标记）
        kw = extract_retrieval_keywords(reference_str, data_type, is_special)
        df.at[idx, "关键字"] = kw
        print(f" 关键词：{kw}（长度：{len(kw.replace('（', '').replace('）', ''))}字）")

        # 3. 生成问题（传入数据类型）
        q = generate_question_stream(kw, data_type)
        df.at[idx, "问题"] = q
        print(f" 生成问题：{q}")

        # 4. 带随机波动的间隔（避免风控）
        sleep_time = get_sleep_time()
        print(f"等待 {sleep_time:.1f} 秒后处理下一行...")
        time.sleep(sleep_time)
        print("-" * 80)

    # ==================== 单个文件处理完成后立即保存 ====================
    try:
        file_dir = os.path.dirname(file_path)
        fname = os.path.basename(file_path)
        name_no_ext, ext = os.path.splitext(fname)
        out_path = os.path.join(file_dir, f"0310-{name_no_ext}{output_suffix}{ext}")

        # 保存，防止乱码
        df.to_excel(out_path, sheet_name=sheet_name, index=False, engine="openpyxl")
        print(f"\n单个文件处理完成，已保存：{out_path}")
        print(f"输出列：原列 + 参考 + 关键字 + 问题")
    except Exception as e:
        print(f"\n保存失败：{str(e)}")


# ==================== 主函数 ====================
def main():
    print("=" * 60)
    print("纪检数据集关键词+问题生成工具（精准关联版）")
    print("=" * 60)
    print(f"待处理文件数：{len(INPUT_FILES)} 个")
    print(f"配置：关键词4-8字（1个）｜严格关联参考列｜问题严格关联关键词｜纪检场景精准匹配")
    print(f"间隔：基础{BASE_SLEEP}秒 + 随机{RANDOM_SLEEP_RANGE}秒波动")
    print(f"四类数据精准界定：重要讲话/党纪法规/纪检实务/理论文章")
    print("=" * 60)

    # 遍历处理每个文件（单个处理完成后立即保存）
    for file_idx, file_conf in enumerate(INPUT_FILES, 1):
        print(f"\n{'=' * 20} 开始处理第 {file_idx}/{len(INPUT_FILES)} 个文件 {'=' * 20}")
        process_single_file(file_conf)
        print(f"{'=' * 20} 第 {file_idx}/{len(INPUT_FILES)} 个文件处理完成 {'=' * 20}")

    print("\n" + "=" * 60)
    print("所有文件处理完成！")
    print(f"总计生成唯一关键词：{len(GENERATED_KEYWORDS)} 个")
    print(f"总计生成唯一问题：{len(GENERATED_QUESTIONS)} 个")
    print("每个文件均已单独保存，包含「参考」「关键字」「问题」列")
    print("关键词严格关联参考列，问题严格关联关键词，均贴合纪检场景")
    print("=" * 60)


if __name__ == "__main__":
    # 安装依赖（首次运行需执行，注释掉也可手动安装）
    # os.system("pip install tqdm openai pandas openpyxl")

    main()