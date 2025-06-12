import h5py
import numpy as np

# 打开TDR文件
tdr_file = '/Users/lihuazhen/Downloads/Diamond_Pipeline/Diamond_Pipeline/Data_link/DWF_Huazhen_c4/1e-3/n1358_000010_des.tdr'

print("=== 分析TDR文件中的大数据集 ===")
print(f"文件: {tdr_file}")

try:
    with h5py.File(tdr_file, 'r') as f:
        state = f['collection/geometry_0/state_0']
        
        # 首先统计所有数据集的大小
        print(f"\n=== 数据集大小统计 ===")
        dataset_sizes = []
        
        for i in range(26):
            dataset_key = f'dataset_{i}'
            if dataset_key in state:
                dataset_group = state[dataset_key]
                for key in dataset_group.keys():
                    item = dataset_group[key]
                    if isinstance(item, h5py.Dataset):
                        size = item.size
                        dataset_sizes.append({
                            'path': f'{dataset_key}/{key}',
                            'size': size,
                            'shape': item.shape,
                            'dtype': item.dtype
                        })
        
        # 按大小排序
        dataset_sizes.sort(key=lambda x: x['size'], reverse=True)
        
        print("数据集按大小排序:")
        for i, ds in enumerate(dataset_sizes[:15]):  # 显示前15个最大的
            print(f"{i+1:2d}. {ds['path']}: {ds['size']:,} 元素, shape={ds['shape']}, dtype={ds['dtype']}")
        
        # 找到最大的数据集
        max_size = dataset_sizes[0]['size']
        large_datasets = [ds for ds in dataset_sizes if ds['size'] == max_size]
        
        print(f"\n=== 最大数据集分析 (元素数: {max_size:,}) ===")
        
        for ds_info in large_datasets:
            path_parts = ds_info['path'].split('/')
            dataset_key = path_parts[0]
            value_key = path_parts[1]
            
            dataset_group = state[dataset_key]
            item = dataset_group[value_key]
            values = item[...]
            
            print(f"\n📄 {ds_info['path']}:")
            print(f"  数值范围: {np.min(values):.6e} 到 {np.max(values):.6e}")
            print(f"  平均值: {np.mean(values):.6e}")
            print(f"  标准差: {np.std(values):.6e}")
            print(f"  非零值: {np.count_nonzero(values):,}/{values.size:,}")
            
            # 权重势特征分析
            close_to_zero = np.sum((values >= -0.01) & (values <= 0.01))
            close_to_one = np.sum((values > 0.9) & (values <= 1.1))
            in_zero_one = np.sum((values >= 0) & (values <= 1))
            negative_values = np.sum(values < 0)
            
            print(f"  接近0的值 (±0.01): {close_to_zero:,}")
            print(f"  接近1的值 (0.9-1.1): {close_to_one:,}")
            print(f"  0-1范围内的值: {in_zero_one:,} ({100*in_zero_one/values.size:.1f}%)")
            print(f"  负值数量: {negative_values:,}")
            
            # 数值分布分析
            if values.size > 0:
                # 找到主要的数值区间
                hist, bin_edges = np.histogram(values, bins=20)
                max_bin_idx = np.argmax(hist)
                main_range = f"[{bin_edges[max_bin_idx]:.3f}, {bin_edges[max_bin_idx+1]:.3f}]"
                print(f"  主要数值区间: {main_range} (包含 {hist[max_bin_idx]:,} 个值)")
                
                # 显示一些样本值
                print(f"  前10个值: {values[:10]}")
                print(f"  中间10个值: {values[len(values)//2:len(values)//2+10]}")
                print(f"  后10个值: {values[-10:]}")
                
                # 检查是否是权重势
                if close_to_one > 1000 and in_zero_one > values.size * 0.8:
                    print(f"  ⭐ 这很可能是权重势数据！")
                elif close_to_zero > values.size * 0.8:
                    print(f"  ⚠️  这可能是数值噪声数据")
                elif np.all(values == values[0]):
                    print(f"  📌 这是常数数据 (值={values[0]})")
        
        # 比较与几何信息
        geometry = f['collection/geometry_0']
        vertex_count = geometry['vertex'].shape[0]
        print(f"\n=== 与几何信息对比 ===")
        print(f"顶点总数: {vertex_count:,}")
        print(f"最大数据集大小: {max_size:,}")
        if max_size == vertex_count:
            print("✅ 最大数据集大小与顶点数匹配 - 这是完整的场数据")
        else:
            print(f"❓ 数据集大小与顶点数不匹配 (差异: {abs(max_size - vertex_count):,})")

except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc() 