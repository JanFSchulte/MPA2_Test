import velox 

def velox_version():
        
        with velox.MessageServerInterface(ipaddr='131.225.90.210',targetSocket=1422) as msgServer:
                v = velox.ReportKernelVersion()
                print('The kernel version is', v.Version, 'and', v.Description)
        return

def lower_needles():

        # Go to contact height        
        with velox.MessageServerInterface(ipaddr='131.225.90.210',targetSocket=1422) as msgServer:

                contactHeight = get_contact_height()
                # Z = go to z coord with respect to zero
                # Y = in units of microns
                velox.MoveChuckZ(contactHeight,'Z','Y')
        print("Chuck moved to contact height")
        return 

def lift_needles():

        # Go to separation height
        with velox.MessageServerInterface(ipaddr='131.225.90.210',targetSocket=1422) as msgServer:

                sepHeight = get_separation_height()
                # Z = go to z coord with respect to zero
                # Y = in units of microns
                velox.MoveChuckZ(sepHeight,'Z','Y')
        print("Chuck moved to separation height")
        return 

def get_contact_height():
        # Y = get distances in microns
        contact, over, alignDist, sepDist, searchDist = velox.ReadChuckHeights('Y')
        return contact
   
def get_alignment_height():
        # Y = get distances in microns
        contact, over, alignDist, sepDist, searchDist = velox.ReadChuckHeights('Y')
        return contact - alignDist

def get_separation_height():
        # Y = get distances in microns
        contact, over, alignDist, sepDist, searchDist = velox.ReadChuckHeights('Y')
        return contact - sepDist

def check_height():
        with velox.MessageServerInterface(ipaddr='131.225.90.210',targetSocket=1422) as msgServer:

                # Y = get distances in microns                                                                                        
                contact, over, alignDist, sepDist, searchDist = velox.ReadChuckHeights('Y')

                x,y,z = velox.ReadChuckPosition('Y')

                if z == 0:
                        return 'CONTACT'
                elif z == 0 - alignDist:
                        return 'ALIGNMENT'
                elif z == 0 - sepDist:
                        return 'SEPARATION'
                else:
                        return 'UNKNOWN'


def step_nMPA(chipid,nMPA):

        with velox.MessageServerInterface(ipaddr='131.225.90.210',targetSocket=1422) as msgServer:

                # Go to separation height
                sepHeight = get_separation_height()
                # Z = go to z coord with respect to zero
                # Y = in units of microns
                velox.MoveChuckZ(sepHeight,'Z','Y')
                
                # MPA width in microns (11.9mm in MPA1 manual)
                width_MPA = 12001
        
                # signed distance to step
                deltax = nMPA * width_MPA
        
                # Speed as percentage of full speed
                speed = 20

                # R = step relative to current position
                # Y = step size in microns
                velox.MoveChuck(deltax, 0, 'R', 'Y', speed)

        return int(chipid) + nMPA
