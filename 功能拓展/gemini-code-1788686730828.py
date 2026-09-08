import os
import yaml
import glob
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def parse_wiki_frontmatter(wiki_dir: str) -> pd.DataFrame:
    """
    遍历 Wiki 目录中的所有 Markdown 文件，提取 YAML Frontmatter 元数据
    """
    records = []
    md_files = glob.glob(os.path.join(wiki_dir, "**/*.md"), recursive=True)
    
    for file_path in md_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    try:
                        metadata = yaml.safe_load(parts[1])
                        if isinstance(metadata, dict):
                            metadata['file_path'] = file_path
                            records.append(metadata)
                    except yaml.YAMLError as e:
                        print(f"Error parsing {file_path}: {e}")
                        
    return pd.DataFrame(records)

# 1. 加载并清洗元数据
df = parse_wiki_frontmatter("./wiki")

# 2. 定量统计：各主流期刊发表的新时代文学重点作品数量
plt.figure(figsize=(10, 5))
sns.countplot(data=df[df['type'] == 'work'], x='first_venue', order=df['first_venue'].value_counts().index)
plt.title("新时代文学重点作品发表阵地分布图", fontsize=14)
plt.xlabel("发表期刊/阵地")
plt.ylabel("作品篇数")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("venue_analysis.png", dpi=300)