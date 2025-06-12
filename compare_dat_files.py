import re
import numpy as np

# 比较正常的DAT文件和有问题的DAT文件
normal_dat = '/Users/lihuazhen/Downloads/Diamond_Pipeline/Diamond_Pipeline/Data_link/DWF_Huazhen_c4/nominal.dat'
problem_dat = '/Users/lihuazhen/Downloads/Diamond_Pipeline/Diamond_Pipeline/Data_link/DWF_Huazhen_c4/1e-3/1e-3_000010_des.dat'

print("=== 比较正常DAT文件 vs 有问题的DAT文件 ===")
print(f"正常文件: {normal_dat}")
print(f"问题文件: {problem_dat}")

def analyze_dat_file(file_path, file_label):
    print(f"\n{'='*80}")
    print(f"分析 {file_label}")
    print(f"{'='*80}")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # 查看文件头部信息
    print("\n=== 文件头部信息 ===")
    lines = content.split('\n')
    for i, line in enumerate(lines[:20]):
        if 'datasets' in line or 'functions' in line:
            print(f"行 {i+1}: {line.strip()}")
    
    # 找到所有Dataset定义
    dataset_pattern = r'Dataset \("([^"]+)"\) \{'
    all_datasets = re.finditer(dataset_pattern, content)
    
    dataset_info = []
    for match in all_datasets:
        dataset_name = match.group(1)
        start_pos = match.start()
        dataset_info.append({
            'name': dataset_name,
            'start_pos': start_pos
        })
    
    print(f"\n找到 {len(dataset_info)} 个数据段:")
    for i, info in enumerate(dataset_info):
        print(f"{i+1:2d}. {info['name']}")
    
    # 专门分析ElectrostaticPotential数据段
    print(f"\n=== ElectrostaticPotential 数据段分析 ===")
    
    electrostatic_datasets = [info for info in dataset_info if info['name'] == 'ElectrostaticPotential']
    print(f"ElectrostaticPotential数据段数量: {len(electrostatic_datasets)}")
    
    for i, info in enumerate(electrostatic_datasets):
        print(f"\n--- ElectrostaticPotential 数据段 {i+1} ---")
        
        # 找到这个数据段的结束位置
        dataset_idx = dataset_info.index(info)
        if dataset_idx < len(dataset_info) - 1:
            end_pos = dataset_info[dataset_idx + 1]['start_pos']
        else:
            end_pos = len(content)
        
        segment = content[info['start_pos']:end_pos]
        
        # 查找validity信息
        validity_match = re.search(r'validity = \[ "([^"]+)" \]', segment)
        region = validity_match.group(1) if validity_match else "未知"
        print(f"区域: {region}")
        
        # 查找Values数据
        values_match = re.search(r'Values \(([0-9]+)\) \{(.*?)\}', segment, re.DOTALL)
        if values_match:
            count = int(values_match.group(1))
            values_text = values_match.group(2)
            print(f"数值数量: {count:,}")
            
            # 提取样本数值进行分析
            values = []
            lines_processed = 0
            for line in values_text.strip().split('\n'):
                line = line.strip()
                if line and not line.startswith('}') and lines_processed < 100:
                    lines_processed += 1
                    nums = line.split()
                    for num in nums:
                        try:
                            val = float(num)
                            values.append(val)
                            if len(values) >= 1000:
                                break
                        except:
                            pass
                    if len(values) >= 1000:
                        break
            
            if values:
                values = np.array(values)
                print(f"分析样本: {len(values):,}")
                print(f"数值范围: {np.min(values):.6e} 到 {np.max(values):.6e}")
                print(f"平均值: {np.mean(values):.6e}")
                print(f"标准差: {np.std(values):.6e}")
                
                # 分析数值分布
                close_to_zero = np.sum(np.abs(values) < 1e-10)
                close_to_one = np.sum((values > 0.9) & (values <= 1.1))
                in_zero_one = np.sum((values >= 0) & (values <= 1))
                negative_values = np.sum(values < 0)
                
                print(f"接近0的值 (±1e-10): {close_to_zero:,} ({100*close_to_zero/len(values):.1f}%)")
                print(f"接近1的值 (0.9-1.1): {close_to_one:,} ({100*close_to_one/len(values):.1f}%)")
                print(f"0-1范围内的值: {in_zero_one:,} ({100*in_zero_one/len(values):.1f}%)")
                print(f"负值: {negative_values:,} ({100*negative_values/len(values):.1f}%)")
                
                # 显示样本值
                print(f"前10个值: {values[:10]}")
                print(f"后10个值: {values[-10:]}")
                
                # 判断数据质量
                if close_to_zero > len(values) * 0.8:
                    print("❌ 主要是数值噪声！")
                    if 'BULK' in region:
                        print("🚨 严重问题: BULK区域的权重势是数值噪声！")
                elif close_to_one > 50 and in_zero_one > len(values) * 0.8:
                    print("✅ 正确的权重势数据")
                    if 'BULK' in region:
                        print("🎯 BULK区域有正确的权重势！")
                elif in_zero_one > len(values) * 0.8 and np.std(values) > 0.1:
                    print("✅ 良好的权重势分布")
                    if 'BULK' in region:
                        print("🎯 BULK区域有良好的权重势分布！")
                elif np.all(np.abs(values - values[0]) < 1e-10):
                    print(f"📌 常数数据 (值={values[0]})")
                else:
                    print("❓ 数据分布不明确")
    
    return dataset_info

# 分析两个文件
normal_info = analyze_dat_file(normal_dat, "正常文件")
problem_info = analyze_dat_file(problem_dat, "问题文件")

# 比较总结
print(f"\n{'='*80}")
print("=== 比较总结 ===")
print(f"{'='*80}")

print(f"\n数据段数量比较:")
print(f"正常文件: {len(normal_info)} 个数据段")
print(f"问题文件: {len(problem_info)} 个数据段")

normal_electrostatic = sum(1 for info in normal_info if info['name'] == 'ElectrostaticPotential')
problem_electrostatic = sum(1 for info in problem_info if info['name'] == 'ElectrostaticPotential')

print(f"\nElectrostaticPotential数据段比较:")
print(f"正常文件: {normal_electrostatic} 个")
print(f"问题文件: {problem_electrostatic} 个")

print(f"\n关键差异:")
print("- 检查BULK区域的权重势数据质量")
print("- 比较数值分布和范围")
print("- 确认哪个文件有正确的0-1权重势分布") 