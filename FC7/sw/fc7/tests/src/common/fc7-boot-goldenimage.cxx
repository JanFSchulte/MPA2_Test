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
    ( "ip,i", boost::program_options::value<std::string>() , "IP address of target board" );

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

      if ( !lVariablesMap.count ( "ip" ) )
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
    std::string lFilename ( "GoldenImage.bin" );

    std::string lURI ( "ipbusudp-2.0://" + lVariablesMap[ "ip" ].as<std::string>() + ":50001" );

    uhal::HwInterface lBoard = uhal::ConnectionManager::getDevice ( "Board", lURI , "file://etc/uhal/fc7_mmc_interface.xml" );
    fc7::MmcPipeInterface lNode = lBoard.getNode< fc7::MmcPipeInterface > ( "buf_test" );

    lFiles = lNode.ListFilesOnSD ();

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

