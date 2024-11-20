# Additional clean files
cmake_minimum_required(VERSION 3.16)

if("${CONFIG}" STREQUAL "" OR "${CONFIG}" STREQUAL "Debug")
  file(REMOVE_RECURSE
  "CMakeFiles\\TFTP_autogen.dir\\AutogenUsed.txt"
  "CMakeFiles\\TFTP_autogen.dir\\ParseCache.txt"
  "TFTP_autogen"
  )
endif()
