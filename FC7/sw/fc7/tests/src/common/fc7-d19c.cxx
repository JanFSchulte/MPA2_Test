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
  bool fIsLoadingFirmware = true;
  bool fIsLoadingFromSD = false;
  bool fIsDeletingFromSD = false;
  uhal::setLogLevelTo ( uhal::Error() );

  boost::program_options::variables_map lVariablesMap;
  {
    boost::program_options::options_description lOptions ( "Commandline parameters" );
    lOptions.add_options()
    ( "help,h", "Produce this help message" )
    ( "list,l", "List all the bit files" )
    ( "ip,i", boost::program_options::value<std::string>() , "IP address of target board" )
    ( "port,p", boost::program_options::value<std::string>() , "Port of target board" )
    ( "filename,f", boost::program_options::value<std::string>(), "Bitfile to upload" )
    ( "delete,d", boost::program_options::value<std::string>(), "Delete file" )
    ( "name,n", boost::program_options::value<std::string>(), "Write file name" );
    
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

      if ( (!lVariablesMap.count ( "ip" )) )
      {
        throw MissingCommandlineParameters();
      }

      if ( lVariablesMap.count ( "list" ) )
      {
	fIsLoadingFirmware = false;
      }

      if ( lVariablesMap.count ( "delete" ) ) 
      {
	fIsLoadingFirmware = false;
	fIsDeletingFromSD = true;
      }

      if ( lVariablesMap.count ( "name" ) && (!lVariablesMap.count ( "filename" )) )
      {
	fIsLoadingFromSD = true;
      }

      if ( fIsLoadingFirmware && (!fIsLoadingFromSD) )
      {
	if(!lVariablesMap.count ( "filename" )) {
        	throw MissingCommandlineParameters();
	} else {
		fIsDeletingFromSD = true;
	}
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
    if(lVariablesMap.count("name")) lFilename = lVariablesMap[ "name" ].as<std::string>(); 
    

    std::string lPort = "50001";
    if(lVariablesMap.count("port")) lPort = lVariablesMap[ "port" ].as<std::string>(); 
    std::string lURI ( "ipbusudp-2.0://" + lVariablesMap[ "ip" ].as<std::string>() + ":" + lPort );
    //std::string lURI ( "chtcp-2.0://localhost:10203?target=" + lVariablesMap[ "ip" ].as<std::string>() + ":" + lPort );


    uhal::HwInterface lBoard = uhal::ConnectionManager::getDevice ( "Board", lURI , "file://etc/uhal/fc7_mmc_interface.xml" );
    fc7::MmcPipeInterface lNode = lBoard.getNode< fc7::MmcPipeInterface > ( "buf_test" );
    lNode.getClient().setTimeoutPeriod(10000);

    std::cout << "Listing files currently on SD" << std::endl;
    lFiles = lNode.ListFilesOnSD ();
    bool lFilePresentOnSD = false;
    for ( std::vector< std::string >::iterator lIt ( lFiles.begin() ) ; lIt != lFiles.end() ; ++lIt ) {
      std::cout << " - " << *lIt << std::endl;
      if( *lIt == lFilename ) lFilePresentOnSD = true;
    }

    if(fIsLoadingFromSD && !lFilePresentOnSD) {
    	std::cout << "Error! File was not found on SD card. Please select the existing file" << std::endl;
	return -1;
    }

    if ( fIsDeletingFromSD ) {
    	if(lVariablesMap.count("delete")) lFilename = lVariablesMap[ "delete" ].as<std::string>(); 
	try {
     		std::cout << "Deleting file " << lFilename << " from SD..." << std::endl;
      		lNode.DeleteFromSD ( lFilename , lPassword );
    	}
    	catch ( std::exception& aExc )
    	{
      		std::cout << "File does not exist?" << std::endl;
    	}
    }

    if ( fIsLoadingFirmware ) 
    {
	if ( !fIsLoadingFromSD ) {
   		fc7::XilinxBitFile lBitFile ( lVariablesMap[ "filename" ].as<std::string>() );
    		std::cout << "Preparing to copy the bit file..." << std::endl;
    		std::cout << lBitFile << " will be copied to SD card as " << lFilename << std::endl;
    		lNode.FileToSD ( lFilename , lBitFile );
	}
    	std::cout << "Resetting FPGA and loading " << lFilename << " on initialisation..." << std::endl;
    	lNode.RebootFPGA ( lFilename , lPassword );
    	std::cout << "Complete." << std::endl;
    }

  }
  catch ( std::exception& aExc )
  {

    uhal::log ( uhal::Error() , "Exception " , uhal::Quote ( aExc.what() ) , " caught at " , ThisLocation() );
    return 1;
  }
}

