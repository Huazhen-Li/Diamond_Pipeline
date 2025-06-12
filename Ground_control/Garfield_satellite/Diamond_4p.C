#include <iostream>
#include <fstream>
#include <sstream>
#include <cmath>
#include <cstdlib>
#include <vector>

#include <sys/mman.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <cerrno>
#include <cstring>

#include <TCanvas.h>
#include <TROOT.h>
#include <TApplication.h>
#include <TSystem.h>
#include <string.h>

#include "TFile.h"
#include "TTree.h"

#include <vector>
#include <iomanip>
#include "TMath.h"

#include "Garfield/MediumDiamond.hh"

#include "Garfield/MediumConductor.hh"
#include "Garfield/ComponentTcad3d.hh"
#include "Garfield/Sensor.hh"

#include "Garfield/AvalancheMC.hh"
#include "Garfield/FundamentalConstants.hh"
#include "Garfield/Random.hh"

#include "Garfield/SolidWire.hh" 
#include "Garfield/GeometrySimple.hh"
#include "Garfield/MediumMagboltz.hh"

#include "Garfield/ComponentNeBem3d.hh"
#include <string>

using namespace Garfield;

// Transfer function


std::vector<double> current_column_data;
double current_hcenter = -999;

void LOAD_COLUMN(double hcenter_um) {
    // If data for this Hcenter is already loaded, no need to reload
    if (abs(current_hcenter - hcenter_um) < 1e-6) {
        return;
    }
    
    std::ifstream file("LUT.csv");
    if (!file.is_open()) {
        std::cerr << "Error opening LUT.csv" << std::endl;
        return;
    }
    
    std::string line;
    int target_col = -1;
    
    // Skip comment lines and find header row (containing z_um,-50.0,-49.0,... columns)
    while (getline(file, line)) {
        if (line.find("z_um,") != std::string::npos) {
            // This is the header row, parse to find the column corresponding to Hcenter
            std::stringstream ss(line);
            std::string cell;
            int col_index = 0;
            
            while (getline(ss, cell, ',')) {
                if (col_index == 0) {
                    // Skip first column (z_um)
                    col_index++;
                    continue;
                }
                
                try {
                    double h_val = std::stod(cell); // Values in CSV are already in μm
                    if (abs(h_val - hcenter_um) < 1e-6) {
                        target_col = col_index;
                        break;
                    }
                } catch (const std::exception& e) {
                    // Skip cells that cannot be parsed
                }
                col_index++;
            }
            break;
        }
    }
    
    if (target_col == -1) {
        std::cerr << "Hcenter " << hcenter_um << " μm not found in LUT" << std::endl;
        file.close();
        return;
    }
    
    // Clear current data
    current_column_data.clear();
    
    // Read all data rows and extract target column
    while (getline(file, line)) {
        // Skip empty lines and comment lines
        if (line.empty() || line[0] == '#') continue;
        
        std::stringstream ss2(line);
        std::string cell2;
        int current_col = 0;
        
        while (getline(ss2, cell2, ',')) {
            if (current_col == target_col) {
                try {
                    double value = std::stod(cell2);
                    current_column_data.push_back(value);
                } catch (const std::exception& e) {
                    current_column_data.push_back(0.0);
                }
                break;
            }
            current_col++;
        }
    }
    
    file.close();
    current_hcenter = hcenter_um;
    std::cout << "Loaded column for Hcenter = " << hcenter_um << " μm, " << current_column_data.size() << " data points" << std::endl;
}

double GET_VALUE(int row_index) {
    if (row_index < 0 || row_index >= current_column_data.size()) {
        return 0.0;
    }
    return current_column_data[row_index];
}

int main(int argc, char * argv[]) {

  TApplication app("app", &argc, argv);
  
  // Get x0, y0, time_step from command line arguments
  if (argc < 4) {
      std::cerr << "Usage: " << argv[0] << " <x0> <y0> <time_step>" << std::endl;
      std::cerr << "  x0, y0: beam position in micrometers" << std::endl;
      std::cerr << "  time_step: time interval in nanoseconds" << std::endl;
      return 1;
  }
  
  const double x0 = std::stod(argv[1]) * 1e-4;  // Convert μm to cm
  const double y0 = std::stod(argv[2]) * 1e-4;  // Convert μm to cm
  const double time_step = std::stod(argv[3]);  // Time step in ns

  // Fixed simulation parameters  
  const double zm = 500.e-4;    // Sensor thickness: 500μm = 0.05cm


  MediumDiamond CVD;
  CVD.SetTemperature(293.15);
  MediumConductor metal;
  metal.SetTemperature(293.15);


 

  // Define timing and readout label
  std::vector<double> times;
  // Generate 21 time points using specified time step
  for (int i = 0; i < 21; ++i) {
    times.push_back(i * time_step); // 0, time_step, 2*time_step, ..., 20*time_step ns
  }
  const std::string label = "sign";
  
  // Import a 3D TCAD field map
  ComponentTcad3d Diamond3D;
  // Load the mesh (.grd file) and electric field (.dat)
  Diamond3D.Initialise("/tmp/DWF_Huazhen_c4/nominal.grd", "/tmp/DWF_Huazhen_c4/nominal.dat");
  
  // First, set the prompt weighting field component (t=0)
  std::cout << "Setting up prompt weighting field (t=0)..." << std::endl;
  std::ostringstream t0_stream;
  t0_stream << std::setfill('0') << std::setw(6) << 0;
  const std::string wpFileName_t0 = "/tmp/DWF_Huazhen_c4/1e-3/1e-3_" + t0_stream.str() + "_des.dat";
  std::cout << "  Loading prompt component: " << wpFileName_t0 << std::endl;
  
  // Set prompt weighting field for t=0 (required before dynamic weighting potentials)
  bool prompt_success = Diamond3D.SetWeightingField("/tmp/DWF_Huazhen_c4/gnd.dat", wpFileName_t0, 1.0, label);
  if (!prompt_success) {
    std::cerr << "Error: Failed to set prompt weighting field component!" << std::endl;
    return 1;
  }
  std::cout << "✓ Prompt weighting field component loaded successfully." << std::endl;
  
  // Load dynamic weighting field maps for different time points (t > 0)
  std::cout << "Loading " << (times.size()-1) << " dynamic weighting field maps..." << std::endl;
  for (int tt = 1; tt < times.size(); ++tt) {  // Start from tt=1, skip t=0
    
    // Create zero-padded string for tt (e.g., 000001, 000002, ..., 000020)
    std::ostringstream tt_stream;
    tt_stream << std::setfill('0') << std::setw(6) << tt;
    const std::string wpFileName = "/tmp/DWF_Huazhen_c4/1e-3/1e-3_" + tt_stream.str() + "_des.dat";
    std::cout << "  Loading time " << times[tt] << " ns: " << wpFileName << std::endl;
    
    bool dynamic_success = Diamond3D.SetDynamicWeightingPotential("/tmp/DWF_Huazhen_c4/gnd.dat", wpFileName,
                                                                  1.0, times[tt], label);
    if (!dynamic_success) {
      std::cerr << "Warning: Failed to load dynamic weighting potential for t=" << times[tt] << " ns" << std::endl;
    }
  }
  std::cout << "All weighting fields loaded successfully." << std::endl;
  
  // Associate the regions in the field map with medium objects
  auto nRegions = Diamond3D.GetNumberOfRegions();
  std::cout << "Number of regions: " << nRegions << std::endl;
  
  // Set medium for different regions
  
  // Associate the silicon regions in the field map with a medium object. 
  //   auto nRegions = Diamond3D.GetNumberOfRegions();
  //   std::cout<<nRegions<<std::endl;

  Diamond3D.SetMedium("Diamond", &CVD);
  Diamond3D.SetMedium("Graphite", &metal);

  Sensor sensor;
  sensor.AddComponent(&Diamond3D);
  sensor.AddElectrode(&Diamond3D, "bias");  // Use the label for dynamic weighting
  sensor.AddElectrode(&Diamond3D, "sign"); 
  sensor.AddElectrode(&Diamond3D, "BULK+junc1BULK");
  sensor.AddElectrode(&Diamond3D, "junc5BULK+BULK");  

  const int nSignalBins = 2000;
  const double tStep = 0.005;
  sensor.SetTimeWindow(0., tStep, nSignalBins);
  // sensor.SetTransferFunction(transfer);
  // Threshold.
  const double thr1 = -1. * ElementaryCharge;  
  std::cout << "Threshold: " << thr1 << " fC\n";

  // Electron/hole transport.
  AvalancheMC drift;
  drift.SetDistanceSteps(1.e-4);
  drift.SetSensor(&sensor);


  // Define Hcenter values that match the LUT
  std::vector<double> hcenter_values;
  for (int h = -50; h <= 550; h += 1) {
      hcenter_values.push_back(h);  // Keep values in μm
  }
  
  // Set nEvents to match number of Hcenter values
  const unsigned int nEvents = hcenter_values.size();
  
  // Create READOUT file with position information
  std::string outfilename = "TPA_simulation_x" + std::to_string(x0*1e6) + "_y" + std::to_string(y0*1e6) + ".txt";
  std::ofstream outfile;
  outfile.open(outfilename, std::ios::out);
  
  std::cout << "Running simulation for " << nEvents << " Hcenter values from " 
            << hcenter_values[0] << " μm to " << hcenter_values.back() << " μm" << std::endl;
  std::cout << "Beam position: x0 = " << x0*1e6 << " μm, y0 = " << y0*1e6 << " μm" << std::endl;
  std::cout << "Time window: 0 to " << (times.size()-1) * time_step << " ns (step: " << time_step << " ns)" << std::endl;

for (unsigned int j = 0; j < nEvents; ++j) {

    sensor.ClearSignal();
    
    // Use predefined Hcenter values from LUT
    const double Hcenter_um = hcenter_values[j];
    const double t0 = 0.0; 

    // Load column data corresponding to this Hcenter
    LOAD_COLUMN(Hcenter_um);
    unsigned int nesum = 0;
    
    std::cout << "Event " << j << ": Hcenter = " << Hcenter_um << " μm" << std::endl;

    // Generate carriers based on TPA distribution from lookup table
    drift.DisablePlotting();
    
    // Loop through all z positions in the LUT data
    for (int z_index = 0; z_index < current_column_data.size(); z_index++) {
      // Z position corresponds to LUT: z_index=0 -> z=0.5μm, z_index=1 -> z=1.5μm, etc.
      double zposition = (z_index + 0.5) * 1e-4;  // Convert μm to cm
      
      if (zposition < 0 || zposition > zm) continue;
      
      // Get carrier density from LUT
      double num_carrier = GET_VALUE(z_index);
      nesum += num_carrier;  // Track total carriers generated

      // Generate electron-hole pairs at (x0, y0, z) position
      for (int rep = 0; rep < num_carrier; rep++) {
        drift.DriftElectron(x0, y0, zposition, t0);
        drift.DriftHole(x0, y0, zposition, t0);
      }
    }

    // sensor.ConvoluteSignals();

    outfile << "Hcenter = " << Hcenter_um << " μm  " << "x0 = " << x0*1e4 << " μm  " << "y0 = " << y0*1e4 << " μm  "<<"TPA_carriers = "<<nesum<<" q_total = "<<nesum * ElementaryCharge<<" fC\n";
    outfile << "********************************************" << "\n";

    for (unsigned int i = 0; i < nSignalBins; ++i) {
      const double t = (i + 0.5) * tStep;
      const double f = sensor.GetSignal(label, i);
      const double fe = sensor.GetElectronSignal(label, i);
      const double fh = sensor.GetIonSignal(label, i);

      outfile << t << "  " << f << "  " << fe << "  " << fh << "\n";
    } 

  }
  outfile.close();

  std::cout<<"DONE !"<<std::endl;
  // app.Run(true);  // Commented out to allow program to exit automatically

}
