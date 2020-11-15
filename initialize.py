from __future__ import print_function
import platform
import subprocess as sp
import sys, os

if platform.system() == "Windows":

    #fetch CPT16.5.8 from simon's repository on iri.columbia.edu
    try:
        print('Fetching CPT...', end=' ') #prints Fetching CPT...  without moving to a new line
        sys.stdout.flush() #Forces above line to print - it normally wouldnt until 'finished' prints
        f= open('delouputu.txt', 'w')
        sp.call(['del', '/s', '/q', 'CPT_batch_installation.exe'],stdout=f, shell=True) #deletes CPT file if you already have it
        f.close()
        sp.call(['curl','-s', 'https://iri.columbia.edu/~simon/CPT/CPT_batch_installation_16.5.8.exe', '--output', './CPT_batch_installation_16.5.8.exe']) #curl is a program that grabs data from a provided website url. -s mutes its output. --output specifies the output file.
        print('     Finished') #prints 'Finished'
    except:
        print("Unexpected error:", sys.exc_info()[0]) #if an error occurs, prints the type of error, helpful for debugging

	try:
		print('Going to install CPT for you - let it install in the default location - write down where it is, the directory containing "CPT_batch.exe" is your "CPTDIR" variable ')
		sp.call(['./CPT_batch_installation_16.5.8.exe'])
	except:
		print('Youre going to need to download CPT from https://iri.columbia.edu/~simon/CPT/CPT_batch_installation_16.5.8.exe and install it yourself' )



    try:
        print('Checking for conda install... ', end='')
        sys.stdout.flush()  #Forces above line to print - it normally wouldnt until 'finished' prints

        pipo = sp.Popen(['conda'], stdout=sp.PIPE)
        output = pipo.communicate()
        print('     finished')

    except:
        print("Unexpected error:", sys.exc_info()[0])
		print('youre going to need to install conda yourself ')

else:

    try:
        flag=0
        print('Checking for gfortran...', end='')
        sys.stdout.flush()
        sp.call(['gfortran', '--version'])
        print('     Finished')
    except:
        print("Unexpected Error: ", sys.exec_info()[0])
        flag = 1
        print("Trying to install gfortran for you... ")
        try:
            sp.call(['brew', 'cask', 'install', 'gfortran'])
            print('     Finished')
        except:
            print('Unexpected Error: ', sys.exec_info()[0])
            print("Maybe you dont have Homebrew? Go install gfortran")

    if flag:
        try:
            print('Checking for gfortran again...', end='')
            sys.stdout.flush()
            sp.call(['gfortran', '--version'])
            print('     we did it lol')
        except:
            print("Unexpected Error: ", sys.exec_info()[0])
            print('gfortran install failed, go install it manually')



    #fetch CPT16.5.8 from simon's repository on iri.columbia.edu
    try:
        print('Fetching CPT...', end=' ') #prints Fetching CPT...  without moving to a new line
        sys.stdout.flush() #Forces above line to print - it normally wouldnt until 'finished' prints
        sp.call(['rm', '-rf', 'CPT.16.5.8.tar.gz']) #deletes CPT file if you already have it
        sp.call(['curl','-s', 'https://iri.columbia.edu/~simon/CPT/CPT.16.5.8.tar.gz', '--output', './CPT.16.5.8.tar.gz']) #curl is a program that grabs data from a provided website url. -s mutes its output. --output specifies the output file.
        print('     Finished') #prints 'Finished'
    except:
        print("Unexpected error:", sys.exc_info()[0]) #if an error occurs, prints the type of error, helpful for debugging


    try:
        print('Decompressing CPT to ./CPT1658...', end='') #prints Decompressing CPT to ./CPT1658...   without moving to a new line
        sys.stdout.flush()  #Forces above line to print - it normally wouldnt until 'finished' prints
        sp.call(['rm', '-rf', 'CPT1658']) #deletes the directory ./CPT1658 if it exists - just so nothing gets messed up
        sp.call(['mkdir', 'CPT1658']) # makes directory ./CPT1658 so we can send CPT files there
        sp.call(['tar','xf', 'CPT.16.5.8.tar.gz', '--directory', 'CPT1658']) #Decompresses the .tar.gz CPT file we just downloaded, sends output to direcotry we just made
        print('     Finished')  #prints 'Finished'
    except:
        print("Unexpected error:", sys.exc_info()[0])


    try:
        comparison_lines = ["gfortran -O2 -frecursive -c -o sggev.o sggev.f","gfortran -O2 -frecursive -c -o sorgtr.o sorgtr.f","gfortran -O2 -frecursive -c -o ssytrs_rook.o ssytrs_rook.f","gfortran -O2 -frecursive -c -o ssyev_2stage.o ssyev_2stage.f","gfortran -O2 -frecursive -c -o dlansy.o dlansy.f","gfortran -O2 -frecursive -c -o dptcon.o dptcon.f","gfortran -O2 -frecursive -c -o dtrti2.o dtrti2.f","gfortran -O2 -frecursive -c -o cgelqf.o cgelqf.f","gfortran -O2 -frecursive -c -o chpevx.o chpevx.f","gfortran -O2 -frecursive -c -o clatrz.o clatrz.f","gfortran -O2 -frecursive -c -o ctrexc.o ctrexc.f","gfortran -O2 -frecursive -c -o zgbbrd.o zgbbrd.f","gfortran -O2 -frecursive -c -o zhetf2_rook.o zhetf2_rook.f","gfortran -O2 -frecursive -c -o zlarfx.o zlarfx.f","gfortran -O2 -frecursive -c -o zsytrf_rk.o zsytrf_rk.f","gfortran -O2 -frecursive -c -o ztprfb.o ztprfb.f","gfortran -O2 -frecursive -c -o dbdsdc.o dbdsdc.f","gfortran -O2 -frecursive -c -o srotmg.o srotmg.f","gfortran -O2 -frecursive -c -o zdscal.o zdscal.f","gfortran -c -O -DDP=1 -DGFORTRAN  -std=f2008 -fall-intrinsics pfv.F95"] #this is for progress checking
        progress = 0

        print('Compiling CPT... {}%'.format(progress), end='') #prints COmpiling CPT
        sys.stdout.flush() #forces above line to print, it wouldn't normally

        sp.call(['make', '-s', 'clean'], cwd='CPT1658/CPT/16.5.8/lapack/lapack') #remakes lapack - fixes up compile errors
        pipo = sp.Popen(['make'], cwd='CPT1658/CPT/16.5.8/lapack/lapack', stdout=sp.PIPE, universal_newlines=True) #remakes lapack - fixes up compile errors)
        for line in iter(pipo.stdout.readline, ""): #checks if each line of the output is in the 'Comparison lines' list above- they are 5% increments of progress
            if line.strip() in comparison_lines:
                progress += 5
                print('\rCompiling CPT... {}%'.format(progress), end='') #prints COmpiling CPT
                sys.stdout.flush() #forces above line to print, it wouldn't normally
        pipo.communicate()
        pipo = sp.Popen(['make'], cwd='CPT1658/CPT/16.5.8/', stdout=sp.PIPE, universal_newlines=True) #compiles CPT using make'
        for line in iter(pipo.stdout.readline, ""):
            if line.strip() in comparison_lines: #if the output line is in the predeterminied group, add 5% to progress (every 105/2100 lines of output this happens)
                progress += 5
                print('\rCompiling CPT... {}%'.format(progress), end='') #prints COmpiling CPT
                sys.stdout.flush() #forces above line to print, it wouldn't normally
        pipo.communicate()
        print('\rCompiling CPT...     Finished') #prints Finished
        f = open('cptdir.txt', 'w')
        sp.call(['pwd'], stdout=f)
        f.close()
        f = open('cptdir.txt', 'r')
        print('Your "cptdir" is {}CPT1658/CPT/16.5.8/'.format(f.read().strip()))
    except sp.CalledProcessError as e:
        print(e.output)
    except:
        print("Unexpected error:", sys.exc_info()[0])

    try:
        print('Checking for conda install... ', end='')
        sys.stdout.flush()  #Forces above line to print - it normally wouldnt until 'finished' prints

        pipo = sp.Popen(['conda'], stdout=sp.PIPE)
        output = pipo.communicate()
        print('     finished')
    except sp.CalledProcessError as e:
        print(e.output)
    except:
        print("Unexpected error:", sys.exc_info()[0])
        try:
            print('Checking for conda install somewhere else... ', end='')
            sys.stdout.flush()
            os.environ['PATH'] = os.path.expanduser('~/miniconda/bin:{}'.format(os.environ['PATH']))
            pipo = sp.Popen(['conda'], stdout=sp.PIPE)
            output = pipo.communicate()
            print('     finished')
        except sp.CalledProcessError as e:
            print(e.output)
        except:
            print("Unexpected error:", sys.exc_info()[0])
            print('Installing Miniconda for you... ')
            sys.stdout.flush()
            f = open(os.path.expanduser('~/miniconda.sh'),'w')
            sp.call(['curl', '-s', 'https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh', '--output', os.path.expanduser('~/miniconda.sh')])#, stdout=f)
            f.close()
            f = open('./miniconda_install_output.txt', 'w')
            sp.call(['bash', os.path.expanduser('~/miniconda.sh'), '-b', '-p', os.path.expanduser('~/miniconda')],stdout=f)
            f.close()
            sys.stdout.write("\033[F")
            print('Installing Miniconda for you...      finished')
            print('Editing your .bash_profile...      finished')
            print('To access conda, jupyter etc, restart your terminal once this script finishes!')
            f = open(os.path.expanduser('~/.bash_profile'), 'a')
            f.write('export PATH=\"{}/miniconda/bin:$PATH\"'.format(os.path.expanduser('~')))
            f.close()
            print('Checking for conda again... ', end='')
            sys.stdout.flush()
            try:
                f = open('./garbage.txt', 'w')
                sp.call(['conda'], stdout=f)
                f.close()
                print('you did it lol')
            except:
                print("Unexpected error:", sys.exc_info()[0])
