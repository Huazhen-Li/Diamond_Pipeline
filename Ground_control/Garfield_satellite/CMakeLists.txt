cmake_minimum_required(VERSION 3.9 FATAL_ERROR)
project(TCAD)
if(NOT TARGET Garfield::Garfield)
  find_package(Garfield REQUIRED)
endif()

# ---Build executable------------------------------------------------------------
add_executable(Diamond_4p Diamond_4p.C)
target_link_libraries(Diamond_4p Garfield::Garfield)


# ---Copy all files locally to the build directory-------------------------------
foreach(_file )
  configure_file(${_file} ${_file} COPYONLY)
endforeach()
