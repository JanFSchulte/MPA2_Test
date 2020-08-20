#include "uhal/uhal.hpp"
#include "uhal/log/log.hpp"


#include <time.h>
#include <unistd.h>
#include <iostream>

#include "fc7/Firmware.hpp"
#include "fc7/MmcPipeInterface.hpp"

#include <boost/program_options.hpp>


ExceptionClass ( MissingCommandlineParameters, "Required command line parameters are missing" );



int main ( int argc, char* argv[] )
{

  uhal::setLogLevelTo ( uhal::Error() );

  boost::program_options::variables_map lVariablesMap;
  {
    boost::program_options::options_description lOptions ( "Commandline parameters" );
    lOptions.add_options()
    ( "help,h", "Produce this help message" )
    ( "ip,i", boost::program_options::value<std::string>() , "IP address of target board" )
    ( "filename,f", boost::program_options::value<std::string>(), "Bitfile to upload" );

    try
    {
      boost::program_options::store ( boost::program_options::parse_command_line ( argc, argv, lOptions ), lVariablesMap );
      boost::program_options::notify ( lVariablesMap );

      if ( lVariablesMap.count ( "help" ) )
      {
        uhal::log ( uhal::Info , "Usage: " , argv[0] , " [OPTIONS]" );
        uhal::log ( uhal::Info , lOptions );
        return 0;
      }

      if ( (!lVariablesMap.count ( "ip" )) || (!lVariablesMap.count ( "filename" )) )
      {
        throw MissingCommandlineParameters();
      }
    }
    catch ( std::exception& e )
    {
      uhal::log ( uhal::Error , "Error: " , uhal::Quote ( e.what() ) );
      uhal::log ( uhal::Error , "Usage: " , argv[0] , " [OPTIONS]" );
      uhal::log ( uhal::Error , lOptions );
      return 1;
    }
  }


  try
  {
    std::vector<std::string> lFiles;
    std::string lPassword ( "RuleBritannia" );
    std::string lFilename ( "UserImage.bin" );


    std::string lURI ( "ipbusudp-2.0://" + lVariablesMap[ "ip" ].as<std::string>() + ":50001" );
    fc7::XilinxBitFile lBitFile ( lVariablesMap[ "filename" ].as<std::string>() );


    uhal::HwInterface lBoard = uhal::ConnectionManager::getDevice ( "Board", lURI , "file://etc/uhal/fc7_mmc_interface.xml" );
    fc7::MmcPipeInterface lNode = lBoard.getNode< fc7::MmcPipeInterface > ( "buf_test" );


    std::cout << std::endl;
    std::cout << "Listing files currently on SD" << std::endl;
    lFiles = lNode.ListFilesOnSD ();
    for ( std::vector< std::string >::iterator lIt ( lFiles.begin() ) ; lIt != lFiles.end() ; ++lIt ) {
      std::cout << " - " << *lIt << std::endl;
    }


    try {
      std::cout << std::endl;
      std::cout << "Deleting file " << lFilename << " from SD..." << std::endl;
      lNode.DeleteFromSD ( lFilename , lPassword );
    }
    catch ( std::exception& aExc )
    {
      std::cout << "File does not exist?" << std::endl;
    }


    std::cout << "Done. Preparing to copy the bit file..." << std::endl << std::endl;
    std::cout << lBitFile;
    std::cout << "will be copied to SD card as " << lFilename << std::endl << std::endl;
    lNode.FileToSD ( lFilename , lBitFile );


    std::cout << std::endl;
    std::cout << "Resetting FPGA and loading " << lFilename << " on initialisation..." << std::endl;
    lNode.RebootFPGA ( lFilename , lPassword );
    std::cout << "Complete." << std::endl;

  }
  catch ( std::exception& aExc )
  {

    uhal::log ( uhal::Error() , "Exception " , uhal::Quote ( aExc.what() ) , " caught at " , ThisLocation() );
    return 1;
  }
}

