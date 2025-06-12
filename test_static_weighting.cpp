#include <iostream>
#include <string>
#include "Garfield/ComponentTcad3d.hh"
#include "Garfield/MediumDiamond.hh"
#include "Garfield/Sensor.hh"

using namespace Garfield;

int main() {
    std::cout << "=== 测试静态权重势设置 ===" << std::endl;
    
    // 创建组件
    ComponentTcad3d Diamond3D;
    
    // 初始化网格和静电场
    std::string grdFile = "/Users/lihuazhen/Downloads/Diamond_Pipeline/Diamond_Pipeline/Data_link/DWF_Huazhen_c4/nominal.grd";
    std::string datFile = "/Users/lihuazhen/Downloads/Diamond_Pipeline/Diamond_Pipeline/Data_link/DWF_Huazhen_c4/nominal.dat";
    
    std::cout << "初始化网格和静电场..." << std::endl;
    if (!Diamond3D.Initialise(grdFile, datFile)) {
        std::cerr << "错误: 无法初始化网格和静电场!" << std::endl;
        return 1;
    }
    std::cout << "✓ 网格和静电场初始化成功" << std::endl;
    
    // 使用SetWeightingPotential设置权重势（正确方法）
    std::string wpFile = "/Users/lihuazhen/Downloads/Diamond_Pipeline/Diamond_Pipeline/Data_link/DWF_Huazhen_c4/1e-3/1e-3_000010_des.dat";
    std::string label = "readout";
    
    std::cout << "\n使用SetWeightingPotential设置权重势..." << std::endl;
    std::cout << "权重势文件: " << wpFile << std::endl;
    
    // 注意：SetWeightingPotential需要两个文件来计算差值
    // 第一个文件：参考文件（通常是接地文件）
    // 第二个文件：权重势文件
    std::string gndFile = "/Users/lihuazhen/Downloads/Diamond_Pipeline/Diamond_Pipeline/Data_link/DWF_Huazhen_c4/gnd.dat";
    
    bool success = Diamond3D.SetWeightingField(gndFile, wpFile, 1.0, label);
    
    if (success) {
        std::cout << "✓ 权重势设置成功!" << std::endl;
        
        // 测试权重势读取
        std::cout << "\n测试权重势读取..." << std::endl;
        
        // 在几个测试点检查权重势值
        std::vector<std::array<double, 3>> testPoints = {
            {0.0, 0.0, 0.0},      // 中心点
            {0.0, 0.0, 50e-4},    // 靠近电极
            {0.0, 0.0, -50e-4},   // 远离电极
            {10e-4, 0.0, 0.0},    // 侧面
            {0.0, 10e-4, 0.0}     // 另一侧面
        };
        
        for (const auto& point : testPoints) {
            double wp = Diamond3D.WeightingPotential(point[0], point[1], point[2], label);
            std::cout << "点 (" << point[0]*1e4 << ", " << point[1]*1e4 << ", " << point[2]*1e4 
                      << ") μm: 权重势 = " << wp << std::endl;
        }
        
        // 检查权重势梯度
        std::cout << "\n测试权重势梯度..." << std::endl;
        double wx, wy, wz;
        Diamond3D.WeightingField(0.0, 0.0, 0.0, wx, wy, wz, label);
        std::cout << "中心点权重势梯度: (" << wx << ", " << wy << ", " << wz << ")" << std::endl;
        
        if (std::abs(wx) > 1e-10 || std::abs(wy) > 1e-10 || std::abs(wz) > 1e-10) {
            std::cout << "✓ 权重势梯度非零，信号计算应该正常!" << std::endl;
        } else {
            std::cout << "⚠️  权重势梯度为零，可能仍有问题" << std::endl;
        }
        
    } else {
        std::cerr << "❌ 权重势设置失败!" << std::endl;
        return 1;
    }
    
    std::cout << "\n=== 测试完成 ===" << std::endl;
    return 0;
} 