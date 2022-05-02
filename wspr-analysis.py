#!/usr/bin/env python3
from datetime import datetime

import os
import tempfile
os.environ['MPLCONFIGDIR'] = tempfile.mkdtemp()
import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import cgi
import cgitb
import json
import re
import sys


def WSPRspots(jstr):
    if not jstr:
        print('Content-type: text/html\n\n')
        print("Parameter Error")
        return

    js = json.loads(jstr)
    
    plots = []
    for p in js['plots']:
        fm = int(datetime.strptime( p['from'], '%Y-%m-%d %H:%M').timestamp())
        to = int(datetime.strptime( p['to'], '%Y-%m-%d %H:%M').timestamp())
        plots.append(
            { 'label':p['label'], 'color':p['color'], 'from':fm, 'to':to, 
            'repo':[], 'dist':[], 'snr':[],
            'avgdist':[], 'avgsnr':[] }
        )

    plots.sort(key=lambda x: x['from'])

    wsprspot = []
    reporter = {}

    for l in js['spots'].split('\n'):
        col = l.split()
        if len(col) == 13:
            call, freq, snr  = col[2], col[3], col[4]
            dft, grid, pwr = col[5], col[6], col[7] 
            rp, rgrid, km, az  = col[8], col[9], col[10], col[11]
            ts =  int(datetime.strptime(col[0]+' '+col[1], '%Y-%m-%d %H:%M').timestamp())
            reporter[rp] = { 'distance': int(km), 'azimath':int(az) }
            wsprspot.append({ 'ts':ts, 'snr':int(snr),'repo':rp})

    wsprspot.sort(key=lambda x: x['ts'])

    i = 0
    for sp in wsprspot:
        while True:
            if i < len(plots):
                if sp['ts'] >= plots[i]['from']:
                    if sp['ts'] <= plots[i]['to']:
                        plots[i]['snr'].append(sp['snr'])
                        plots[i]['repo'].append(sp['repo'])
                        plots[i]['dist'].append(reporter[sp['repo']]['distance'])
                        break
                    else:
                        i += 1
                        continue
                else:
                    break
            else:
                break

    rpts = None
    for p in plots:
        if not rpts:
            rpts = set(p['repo'])
        else:
            rpts = rpts & set(p['repo'])

    cmnrptr = {}
    for stn in rpts:
        cmnrptr[stn] = { 
            'dist': reporter[stn]['distance'],
            'snr':[ [] for n in range(0, len(plots))]
        }

    cmnlst = sorted(list(cmnrptr),key=lambda x: cmnrptr[x]['dist'])

    i = 0
    for sp in wsprspot:
        while True:
            if i < len(plots):
                if sp['ts'] >= plots[i]['from']:
                    if sp['ts'] <= plots[i]['to']:
                        if sp['repo'] in rpts:
                            cmnrptr[sp['repo']]['snr'][i].append(sp['snr'])
                        break
                    else:
                        i += 1
                        continue
                else:
                    break
            else:
                break

    fig, axes = plt.subplots(1, 1)

    fig.set_figwidth(int(js['width'])/120)
    
    for rp in cmnlst:
        for j in range(0,i):
            l = cmnrptr[rp]['snr'][j]
            if len(l) > 0:
                plots[j]['avgsnr'].append(sum(l)/len(l))
            else:
                plots[j]['avgsnr'].append(0)
            plots[j]['avgdist'].append(cmnrptr[rp]['dist'])
        
    for p in plots:
        x = p['dist']
        y = p['snr']
        axes.scatter(x, y, label=p['label']+f" {len(p['snr'])}spots",c=p['color'],marker='o',alpha=0.8)
        x = p['avgdist']
        y = p['avgsnr']
        axes.plot(x, y,c=p['color'],marker='x',alpha=0.2)

    axes.set_title(js['title'])
    axes.set_xlabel('Distance (km)')
    axes.set_ylabel('SNR (dB)')
    axes.grid()
    axes.legend()
    
    sys.stdout.buffer.write(b'Content-type: image/svg+xml\r\n')
    sys.stdout.buffer.write(b'\r\n')
    plt.savefig(sys.stdout.buffer, format='svg')
    
def main():
    cgitb.enable(display=1, logdir='/tmp')
    form = cgi.FieldStorage()
    
    arg = form.getvalue("arg",None)

    WSPRspots(arg)

if __name__ == '__main__':
    main()
