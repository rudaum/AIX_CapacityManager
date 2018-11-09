#!/usr/bin/python
# - Purpose:
#       To convert range of dates
# - Author:
#       Rudolf Wolter
# - Contact for questions and/or comments:
#       rudolf.wolter@kuehne-nagel.com
# - Parameters:
#       < accepted arguments>
# - Version Releases and modifications.
#       <versions history log>


### START OF MODULE IMPORTS
# --------------------------------------------------------------- #
from os import path, system
from datetime import time, datetime
from subprocess import Popen, PIPE
from optparse import OptionParser
from lib.dblib import mk_dbbenv, Vmstat, Lparstat
# --------------------------------------------------------------- #
### END OF MODULE IMPORTS

### START OF GLOBAL VARIABLES DECLARATION
# --------------------------------------------------------------- #
PEAKSTART = time(8, 00)
PEAKSTOP = time(20, 00)
TRESHOLDW = 20
TRESHOLDC = 8
VMSTATSOURCEDIR = '/ib/dat/kn/statistic/vmstat'
LPARSTATSOURCEDIR = '/admin/stats/lparstat'
REPORTDIR = path.dirname(path.realpath(__file__)) + '/reports'
BASELINE = ['sindbad', 'ibaz', 'parisade', 'ibcomtest',
            'salomo', 'alibaba', 'maruf', 'ibedi1', 'ibedi2',
            'ibedi3', 'ibedi4', 'ibcom1', 'ibcom2', 'ibcom3']
# --------------------------------------------------------------- #
### END OF GLOBAL VARIABLES DECLARATION\

### START OF FUNCTIONS DECLARATION
# --------------------------------------------------------------- #
def parse_args():
    """
    Purpose:
        To parse the scripts given arguments and to generate a dictionary with the values.
    Returns:
        options: A Dictionary with all given, validated arguments.
    Parameters:
    """
    parser = OptionParser(usage='-h | -s [ ALL | servername ]')

    # Declaring Arguments
    parser.add_option("-s", "--server", dest="server",
                      help="ALL to retrieve from all servers or server name to retrieve from a singular server")

    (opts, pargs) = parser.parse_args()
    if not opts.server:
        parser.error('Server Name not given. Use ALL for all servers or provide a single name')

    # if not particular server is given, retrieve from ALL
    if vars(opts)['server'].lower() == 'all':
        return BASELINE
    else:
        return eval("['" + (vars(opts)['server']) + "']")
# --------------------------------------------------------------- #
# --------------------------------------------------------------- #
def retrieve_files(_server):
    """
    Purpose:
        To retrieve vmstat files from a server
    Returns:
        options: A Dictionary with all given, validated arguments.
    Parameters:
        server - Server where the files will be retrieved
    """
    # Retrieving vmstat data
    print('Trying to retrieve vmstat files from {} ...'.format(_server))
    system("/usr/bin/rsync -avz {}:{}/*.dat* {}/{}/ 2>/dev/null".format(server, VMSTATSOURCEDIR, REPORTDIR, _server))
    print('Success!')

    # Retrieving lparstat data
    print('Trying to retrieve lparstat files from {} ...'.format(_server))
    system("/usr/bin/rsync -avz {}:{}/*.dat* {}/{}/ 2>/dev/null".format(_server, LPARSTATSOURCEDIR, REPORTDIR, _server))
    print('Success!')

    # Decompressing Any dat.gz files
    print('Decompressing any compressed files ...')
    cmd = 'find {}/{} -type f -name "*.dat.gz" | ' \
          'while read gzip; do ' \
          '    if [[ ! -f {} ]]; then ' \
          '        gzip -cfd $gzip > {};' \
          '    fi;' \
          'done'.format(REPORTDIR, _server, '${gzip:0:-3}', '${gzip:0:-3}')
    system(cmd)
    print('Success!')
# --------------------------------------------------------------- #
# --------------------------------------------------------------- #
def vmstat_persist(_server):
    """
    Purpose:
        To persist the averages extracted from the vmstat files in the DB, so it can be read by the Report Generator.
    Returns:
        N/A
    Parameters:
        _server - The server the vmstat files were collected from
    """

    serverdir = REPORTDIR + "/" + _server
    cmd = '/usr/bin/ls {}/vmstat*.dat'.format(serverdir)

    # Querying all entries from Vmstat Table
    vmstatobjs = Vmstat().query_all()

    for vmstat_file in Popen(cmd, stdin=PIPE, stdout=PIPE, shell=True).stdout.readlines():
        vmstat_file = vmstat_file.strip('\n')
        persist = True
        not_persisted_msg = ''
        pholder, srvname, d8str = path.basename(vmstat_file).strip('.dat').split('_')
        d8 = datetime.strptime(d8str, '%Y%m%d')
        objid = '{}_{}'.format(_server, d8str)
        today = datetime.now().date()

        # Skipping if file is from today, as it  can be incomplete.
        if '{}'.format(today.strftime('%d-%m-%Y')) == '{}'.format(d8.strftime('%d-%m-%Y')):
            persist = False
            not_persisted_msg = 'Skipping {}. Today\'s file may not yet be complete.'.format(vmstat_file)

        # Skipping if file exists in DB already
        if objid in vmstatobjs.keys():
            persist = False
            not_persisted_msg = 'Skipping {}. Already present in DB.'.format(vmstat_file)

        if persist:
            print('Processing {}'.format(vmstat_file))
            # Grepping $1=Run Queue, $17=idle CPU
            cmd = "grep ':' " + vmstat_file + " | egrep -v 'System configuration' | awk '{print $1, $4, $5, $17, $NF}'"
            output = Popen(cmd, stdin=PIPE, stdout=PIPE, shell=True).stdout.readlines()
            samples = []
            tsholdw = []
            tsholdc = []
            peak_tsholdw = []
            peak_tsholdc = []
            peak_samples = []
            prepeak_tsholdw = []
            prepeak_tsholdc = []
            prepeak_samples = []
            pospeak_tsholdw = []
            pospeak_tsholdc = []
            pospeak_samples = []
            day = d8.strftime('%d-%m-%Y')

            runqueue = avm = freemem = ''
            for count, item in enumerate(output):
                runqueue, avm, freemem, idle, timestamp = item.split(' ')
                idle = int(idle)
                h, m, s = [int(x) for x in timestamp.strip().split(':')]
                timestamp = time(h, m, s)

                # Only consider Business Hours
                if PEAKSTART <= timestamp <= PEAKSTOP:
                    peak_samples.append(idle)
                    # if idle is less than Critical Threshold, append to Critical List, with timestamp
                    if idle <= TRESHOLDC:
                        peak_tsholdc.append((idle, timestamp.strftime('%H:%M:%S')))
                    # if idle is less than Warning Threshold, append to Warning List, with timestamp
                    elif TRESHOLDC < idle <= TRESHOLDW:
                        peak_tsholdw.append((idle, timestamp.strftime('%H:%M:%S')))

                # Before Business Hours
                elif timestamp < PEAKSTART:
                    prepeak_samples.append(idle)
                    # if idle is less than Critical Threshold, append to Critical List, with timestamp
                    if idle <= TRESHOLDC:
                        prepeak_tsholdc.append((idle, timestamp.strftime('%H:%M:%S')))
                    # if idle is less than Warning Threshold, append to Warning List, with timestamp
                    elif TRESHOLDC < idle <= TRESHOLDW:
                        prepeak_tsholdw.append((idle, timestamp.strftime('%H:%M:%S')))

                # After Business Hours
                elif timestamp > PEAKSTOP:
                    pospeak_samples.append(idle)
                    # if idle is less than Critical Threshold, append to Critical List, with timestamp
                    if idle <= TRESHOLDC:
                        pospeak_tsholdc.append((idle, timestamp.strftime('%H:%M:%S')))
                    # if idle is less than Warning Threshold, append to Warning List, with timestamp
                    elif TRESHOLDC < idle <= TRESHOLDW:
                        pospeak_tsholdw.append((idle, timestamp.strftime('%H:%M:%S')))

            try:

                # Reuniting the data for the whole day: pre + peak + pos
                # Pre Peak
                samples.extend(prepeak_samples)
                tsholdw.extend(prepeak_tsholdw)
                tsholdc.extend(prepeak_tsholdc)

                # Peak
                samples.extend(peak_samples)
                tsholdw.extend(peak_tsholdw)
                tsholdc.extend(peak_tsholdc)

                # Pos Peak
                samples.extend(pospeak_samples)
                tsholdw.extend(pospeak_tsholdw)
                tsholdc.extend(pospeak_tsholdc)

                # Creating the averages of the WHOLE day: pre + peak + pos
                avgthshw = round(len(tsholdw) / round(len(samples), 2) * 100, 2)
                avgthshc = round(len(tsholdc) / round(len(samples), 2) * 100, 2)
                avgday = 100 - (round(sum(samples, 0.00) / len(samples), 2))

                # Creating the Averages of the PEAK hours of the day
                peak_avgthshw = round(len(peak_tsholdw) / round(len(peak_samples), 2) * 100, 2)
                peak_avgthshc = round(len(peak_tsholdc) / round(len(peak_samples), 2) * 100, 2)
                peak_avgday = 100 - (round(sum(peak_samples, 0.00) / len(peak_samples), 2))

                # Creating the overall list, with days and tuples
                overall.append((day, peak_avgday, peak_avgthshw, peak_avgthshc))

                # Creating the Relational Object for the Database
                vmobj = Vmstat()
                vmobj.id = objid
                vmobj.servername = _server
                vmobj.date = '{}.{}.{}'.format(d8.year, d8.month, d8.day)
                vmobj.peak_avg_busy = peak_avgday
                vmobj.peak_avg_warning = peak_avgthshw
                vmobj.peak_avg_critical = peak_avgthshc
                vmobj.peak_samples_count = len(peak_samples)
                vmobj.peak_warn_count = len(peak_tsholdw)
                vmobj.peak_crit_count = len(peak_tsholdc)
                vmobj.peakstart = PEAKSTART
                vmobj.peakstop = PEAKSTOP
                vmobj.average_busy = avgday
                vmobj.average_warning = avgthshw
                vmobj.average_critical = avgthshc
                vmobj.samples_count = len(samples)
                vmobj.warn_count = len(tsholdw)
                vmobj.crit_count = len(tsholdc)
                vmobj.runqueue = runqueue
                vmobj.avm = avm
                vmobj.freemem = freemem

                # Persisting the Object in the Database
                vmobj.update()
            except ZeroDivisionError:
                print 'Vmstat data not found for file {}:'.format(vmstat_file.strip())

            # persisting in a file
            listfile = open(REPORTDIR + '/' + _server + '/' + _server + '_vmstat.list', 'w')
            listfile.write(str(overall))
            listfile.close()
        else:
            print(not_persisted_msg)
# --------------------------------------------------------------- #
# --------------------------------------------------------------- #
def lparstat_persist(_server):
    """
    Purpose:
        To persist the averages extracted from the lparstat files in the DB, so it can be read by the Report Generator.
    Returns:
        N/A
    Parameters:
        _server - The server the lparstat files were collected from
    """

    serverdir = REPORTDIR + "/" + _server
    cmd = '/usr/bin/ls {}/lparstat*.dat'.format(serverdir)

    # Querying all entries from lparstat Table
    lparstatobjs = Lparstat().query_all()

    for lparstat_file in Popen(cmd, stdin=PIPE, stdout=PIPE, shell=True).stdout.readlines():
        lparstat_file = lparstat_file.strip('\n')
        persist = True
        not_persisted_msg = ''
        pholder, srvname, d8str = path.basename(lparstat_file).strip('.dat').split('_')
        d8 = datetime.strptime(d8str, '%Y%m%d')
        objid = '{}_{}'.format(_server, d8str)
        today = datetime.now().date()

        # Skipping if file is from today, as it  can be incomplete.
        if '{}'.format(today.strftime('%d-%m-%Y')) == '{}'.format(d8.strftime('%d-%m-%Y')):
            persist = False
            not_persisted_msg = 'Skipping {}. Today\'s file may be not yet complete.'.format(lparstat_file)

        # Skipping if file exists in DB already
        if objid in lparstatobjs.keys():
            persist = False
            not_persisted_msg = 'Skipping {}. Already present in DB.'.format(lparstat_file)

        if persist:
            print('Processing {}'.format(lparstat_file))

            # Grepping CPU_mode, CPU_type, SMT and Logical processors
            cmd = "grep '^System configuration' " + lparstat_file + " | " \
                  "awk '{" \
                  "   if(substr($NF, 1, 4) ==" + '"mem="' + ") {" \
                  "      $NF=" + '"DED"' \
                  "   } else " \
                  "      $NF=substr($NF, 5)" \
                  "} " \
                  "{print substr($3, 6), substr($4, 6), substr($5, 5), substr($6, 6), $NF}'"

            output = Popen(cmd, stdin=PIPE, stdout=PIPE, shell=True).stdout.read().strip()
            ctype, cmode, csmt, lprocs, centc = output.split()
            vprocs = 0

            # Translating SMT to a number
            if csmt.lower() == 'on':
                csmt = 2
            elif csmt.lower() == 'off':
                csmt = 1
            if str(csmt).isdigit():
                vprocs = int(lprocs) / int(csmt)

            # Setting entc, if server is in dedicated mode.
            if centc == 'DED':
                centc = vprocs

            # Different Query Approach if Shared or dedicated Modes
            if ctype.lower() == 'shared':
                # Grepping $4=idle CPU, $5=physc, $6=entc, $NF=timestamp
                cmd = "grep ':' " + lparstat_file + " | egrep -v 'System configuration' | awk '{print $4, $5, $6, $NF}'"
            else:
                # Grepping $4=idle CPU, $NF=timestamp
                cmd = "grep ':' {} | egrep -v 'System configuration' | awk '{}print $4, {}-({}*$4/100), 100, $NF{}'"\
                      .format(lparstat_file, '{', vprocs, vprocs, '}')

            output = Popen(cmd, stdin=PIPE, stdout=PIPE, shell=True).stdout.readlines()
            physc_samples = []
            peak_physc_samples = []
            prepeak_physc_samples = []
            pospeak_physc_samples = []
            entc_samples = []
            peak_entc_samples = []
            prepeak_entc_samples = []
            pospeak_entc_samples = []
            idle_samples = []
            idle_tsholdw = []
            idle_tsholdc = []
            peak_idle_tsholdw = []
            peak_idle_tsholdc = []
            peak_idle_samples = []
            prepeak_idle_samples = []
            prepeak_idle_tsholdw = []
            prepeak_idle_tsholdc = []
            pospeak_idle_samples = []
            pospeak_idle_tsholdw = []
            pospeak_idle_tsholdc = []

            for count, item in enumerate(output):
                idle = float(item.split(' ')[0])
                physc = float(item.split(' ')[1])
                entc = float(item.split(' ')[2])
                timestamp = item.split(' ')[3]
                h, m, s = [int(x) for x in timestamp.strip().split(':')]
                timestamp = time(h, m, s)

                # Only consider Business Hours
                if PEAKSTART <= timestamp <= PEAKSTOP:
                    peak_physc_samples.append(physc)
                    peak_entc_samples.append(entc)
                    peak_idle_samples.append(idle)
                    if idle <= TRESHOLDC:
                        peak_idle_tsholdc.append((idle, timestamp.strftime('%H:%M:%S')))
                    # if idle is less than Warning Threshold, append to Warning List, with timestamp
                    elif TRESHOLDC < idle <= TRESHOLDW:
                        peak_idle_tsholdw.append((idle, timestamp.strftime('%H:%M:%S')))

                # Before Business Hours
                elif timestamp < PEAKSTART:
                    prepeak_physc_samples.append(physc)
                    prepeak_entc_samples.append(entc)
                    prepeak_idle_samples.append(idle)
                    if idle <= TRESHOLDC:
                        prepeak_idle_tsholdc.append((idle, timestamp.strftime('%H:%M:%S')))
                    # if idle is less than Warning Threshold, append to Warning List, with timestamp
                    elif TRESHOLDC < idle <= TRESHOLDW:
                        prepeak_idle_tsholdw.append((idle, timestamp.strftime('%H:%M:%S')))

                # After Business Hours
                elif timestamp > PEAKSTOP:
                    pospeak_physc_samples.append(physc)
                    pospeak_entc_samples.append(entc)
                    pospeak_idle_samples.append(idle)
                    if idle <= TRESHOLDC:
                        pospeak_idle_tsholdc.append((idle, timestamp.strftime('%H:%M:%S')))
                    # if idle is less than Warning Threshold, append to Warning List, with timestamp
                    elif TRESHOLDC < idle <= TRESHOLDW:
                        pospeak_idle_tsholdw.append((idle, timestamp.strftime('%H:%M:%S')))

            try:
                # Reuniting the data for the whole day: pre + peak + pos
                # Pre Peak
                physc_samples.extend(prepeak_physc_samples)
                entc_samples.extend(prepeak_entc_samples)
                idle_samples.extend(prepeak_idle_samples)
                idle_tsholdw.extend(prepeak_idle_tsholdw)
                idle_tsholdc.extend(prepeak_idle_tsholdc)

                # Peak
                physc_samples.extend(peak_physc_samples)
                entc_samples.extend(peak_entc_samples)
                idle_samples.extend(peak_idle_samples)
                idle_tsholdw.extend(peak_idle_tsholdw)
                idle_tsholdc.extend(peak_idle_tsholdc)

                # Pos Peak
                physc_samples.extend(pospeak_physc_samples)
                entc_samples.extend(pospeak_entc_samples)
                idle_samples.extend(pospeak_idle_samples)
                idle_tsholdw.extend(pospeak_idle_tsholdw)
                idle_tsholdc.extend(pospeak_idle_tsholdc)

                # Creating the averages of the WHOLE day: pre + peak + pos
                physc_avgday = round(sum(physc_samples, 0.00) / len(physc_samples), 2)
                entc_avgday = round(sum(entc_samples, 0.00) / len(entc_samples), 2)
                idle_avgday = round(sum(idle_samples, 0.00) / len(idle_samples), 2)
                avg_warning = round(len(idle_tsholdw) / round(len(idle_samples), 2) * 100, 2)
                avg_critical = round(len(idle_tsholdc) / round(len(idle_samples), 2) * 100, 2)

                # Creating the Averages of the PEAK hours of the day
                peak_physc_avgday = round(sum(peak_physc_samples, 0.00) / len(peak_physc_samples), 2)
                peak_entc_avgday = round(sum(peak_entc_samples, 0.00) / len(peak_entc_samples), 2)
                peak_idle_avgday = round(sum(peak_idle_samples, 0.00) / len(peak_idle_samples), 2)
                peak_avg_warning = round(len(peak_idle_tsholdw) / round(len(peak_idle_samples), 2) * 100, 2)
                peak_avg_critical = round(len(peak_idle_tsholdc) / round(len(peak_idle_samples), 2) * 100, 2)

                # Creating the Relational Object for the Database
                lpobj = Lparstat()
                lpobj.id = objid
                lpobj.servername = _server
                lpobj.date = '{}.{}.{}'.format(d8.year, d8.month, d8.day)
                lpobj.ent_cap = centc
                lpobj.vprocs = vprocs
                lpobj.cpu_type = ctype
                lpobj.cpu_mode = cmode
                lpobj.peak_avg_physc = peak_physc_avgday
                lpobj.peak_average_entc = peak_entc_avgday
                lpobj.peak_average_idle = peak_idle_avgday
                lpobj.peak_avg_idle_warning = peak_avg_warning
                lpobj.peak_avg_idle_critical = peak_avg_critical
                lpobj.peak_samples_count = len(peak_physc_samples)
                lpobj.peakstart = PEAKSTART
                lpobj.peakstop = PEAKSTOP
                lpobj.average_physc = physc_avgday
                lpobj.samples_count = len(physc_samples)
                lpobj.average_idle = idle_avgday
                lpobj.avg_idle_warning = avg_warning
                lpobj.avg_idle_critical = avg_critical
                lpobj.average_entc = entc_avgday

                # Persisting the Object in the Database
                lpobj.update()
            except ZeroDivisionError:
                print 'lparstat data Error for file {}:'.format(lparstat_file.strip())
        else:
            print(not_persisted_msg)
# --------------------------------------------------------------- #
### END OF FUNCTIONS DECLARATION

### START OF CLASS DEFINITIONS
# --------------------------------------------------------------- #
# --------------------------------------------------------------- #
### END OF CLASS DEFINITIONS


### START OF MAIN PROGRAM
serverlist = parse_args()
mk_dbbenv()

for server in serverlist:
    print('Generating reports for {} ... It may take a while.'.format(server))
    overall = []

    # --- Retrieving STAT files from remove servers
    retrieve_files(server)

    # --- Processing VMSTAT files and persisting the averages
    vmstat_persist(server)

    # --- Processing LPARSTAT files and persisting the averages
    lparstat_persist(server)

print('Success!')
### END OF MAIN PROGRAM
