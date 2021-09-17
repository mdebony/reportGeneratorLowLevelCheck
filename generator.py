import os
from os.path import join
import pandas as pd
import copy
import datetime
import tqdm

def latex_table(content_table):
    str_table = '\\begin{center}\n'
    str_table += '\t\\begin{longtable}{|l|'+'c|'*(len(content_table[0])-1)+'}\n'
    str_table += '\t\t\hline\n'
    for i in range(len(content_table)):
        str_table += '\t\t'
        for j in range(len(content_table[i])):
            str_table += content_table[i][j]
            if j < (len(content_table[i])-1):
                str_table += ' & '
        str_table += ' \\\ \hline\n'
    str_table += '\t\end{longtable}\n'
    str_table += '\end{center}\n'
    return str_table

def find_figure(list_figure, template):
    for i in range(len(list_figure)):
        if template in list_figure[i]:
            return list_figure[i]
    return ''

def generator_pdf(input_db_file, runlist_folder, lowlevel_folder, report_folder, delete_tex_files=True):
    db = pd.read_csv(input_db_file)
    
    with open('template.tex') as template_file:
        template = template_file.read()
        
    for i in tqdm.tqdm(db.index):
        report = copy.deepcopy(template)
        
        full_analysis_name = db.loc[i, 'name_analysis']
        if db.loc[i, 'analysis_profile'] == 'hess1_stereo_loose':
            full_analysis_name += '_HESSI_Stereo_Loose'
        elif db.loc[i, 'analysis_profile'] == 'hess2_mono_loose':
            full_analysis_name += '_HESSII_Mono_Loose'
        elif db.loc[i, 'analysis_profile'] == 'hess2_stereo_loose':
            full_analysis_name += '_HESSII_Stereo_Loose'
        else:
            print(db.loc[i, 'analysis_profile'], 'unknown profile ')
            continue
            
        dir_analysis = join(lowlevel_folder, full_analysis_name)
        
        time_burst = datetime.datetime.fromisoformat(db.loc[i, 'time_burst'])
        delay = datetime.timedelta(seconds=int(db.loc[i, 'delay']))
        duration = datetime.timedelta(seconds=int(db.loc[i, 'time_span']))
        
        
        report = report.replace('%figurepath%', dir_analysis+'/')
        report = report.replace('%title%', db.loc[i, 'name_grb'] + ' \\\ \small{' + db.loc[i, 'name_analysis'][len(db.loc[i, 'name_grb'])+1:] + '}')
        report = report.replace('%alert_instrument%', db.loc[i, 'detection_instrument'])
        report = report.replace('%altertime%', str(time_burst))
        report = report.replace('%startime%', str(time_burst+delay))
        if delay.total_seconds() < 7200.:
            report = report.replace('%delay%', '{:.1f}'.format(delay.total_seconds()/60) + ' min')
        else:
            report = report.replace('%delay%', '{:.1f}'.format(delay.total_seconds()/3600) + ' h')
        report = report.replace('%duration%', '{:.1f}'.format(duration.total_seconds()/60) + ' min')
        
        
        if os.path.isfile(join(runlist_folder, db.loc[i, 'name_analysis']+'.list')):
            with open(join(runlist_folder, db.loc[i, 'name_analysis']+'.list')) as runlist_file:
                tmp_runlist = runlist_file.readlines()
                runlist = []
                for j in range(len(tmp_runlist)):
                    runlist.append(int(tmp_runlist[j]))
        else:
            continue
        runlist_str = ''
        for j in range(len(runlist)):
            runlist_str += '\t\item '+str(runlist[j])
        report = report.replace('%runlist%', runlist_str)
        
        available_figure = os.listdir(dir_analysis)
        for j in range(len(available_figure)-1, -1, -1):
            if available_figure[j][-4:] != '.png':
                available_figure.pop(j)
                
        nsb_table = [['Telescope', 'Map', 'Distribution'],]
        nsb_table.append(['All', 
                          '\includegraphics[width=0.4\linewidth]{'+find_figure(available_figure, 'NSB_SkyInfo')+'}', 
                          '\includegraphics[width=0.4\linewidth]{'+find_figure(available_figure, 'NSBMap_os_grxy')+'}'])
        if db.loc[i, 'analysis_profile'] == 'hess1_stereo_loose' or db.loc[i, 'analysis_profile'] == 'hess2_stereo_loose':
            for j in range(1, 5):
                nsb_table.append(['CT'+str(j), 
                                  '\includegraphics[width=0.4\linewidth]{'+find_figure(available_figure, 'NSB_CT'+str(j)+'_SkyInfo')+'}', 
                                  '\includegraphics[width=0.4\linewidth]{'+find_figure(available_figure, 'NSB_CT'+str(j)+'_os_grxy')+'}'])
        if db.loc[i, 'analysis_profile'] == 'hess2_mono_loose' or db.loc[i, 'analysis_profile'] == 'hess2_stereo_loose':
            nsb_table.append(['CT5', 
                              '\includegraphics[width=0.4\linewidth]{'+find_figure(available_figure, 'NSB_CT5_SkyInfo')+'}', 
                              '\includegraphics[width=0.4\linewidth]{'+find_figure(available_figure, 'NSB_CT5_os_grxy')+'}'])
        report = report.replace('%NSB%', latex_table(nsb_table))
        
        nsb_table = [['Run', 'Trigger'],]
        for j in range(len(runlist)):
            nsb_table.append(['Run '+str(runlist[j]), 
                              '\includegraphics[width=0.85\linewidth]{'+find_figure(available_figure, 'Run'+str(runlist[j])+'_RecomputedTriggerRateVsTime')+'}'])
        report = report.replace('%trigger%', latex_table(nsb_table))
        
        calibration_str = ''
        for k in range(len(runlist)):
            calibration_str += '\subsection{Run '+str(runlist[k])+'}\n\n'
            calibration_table = [['Telescope', 'BP Timeline', 'BP Map', 'COG map', 'Pixel partipation'],]
            if db.loc[i, 'analysis_profile'] == 'hess1_stereo_loose' or db.loc[i, 'analysis_profile'] == 'hess2_stereo_loose':
                for j in range(1, 5):
                    calibration_table.append(['CT'+str(j),
                                              '\includegraphics[width=0.2\linewidth]{'+find_figure(available_figure, 'Run'+format(runlist[k], '06')+'_CT'+str(j)+'_CalibTimeLines')+'}',
                                              '\includegraphics[width=0.2\linewidth]{'+find_figure(available_figure, 'Run_'+str(runlist[k])+'_CT'+str(j)+'_CalibrationStatus')+'}',
                                              '\includegraphics[width=0.2\linewidth]{'+find_figure(available_figure, 'Run_'+str(runlist[k])+'_CT'+str(j)+'_CogMap')+'}',
                                              '\includegraphics[width=0.2\linewidth]{'+find_figure(available_figure, 'Run_'+str(runlist[k])+'_CT'+str(j)+'_ShowerParticipation')+'}'])
            if db.loc[i, 'analysis_profile'] == 'hess2_mono_loose' or db.loc[i, 'analysis_profile'] == 'hess2_stereo_loose':
                calibration_table.append(['CT5', 
                                          '\includegraphics[width=0.2\linewidth]{'+find_figure(available_figure, 'Run'+format(runlist[k], '06')+'_CT5_CalibTimeLines')+'}',
                                          '\includegraphics[width=0.2\linewidth]{'+find_figure(available_figure, 'Run_'+str(runlist[k])+'_CT5_CalibrationStatus')+'}',
                                          '\includegraphics[width=0.2\linewidth]{'+find_figure(available_figure, 'Run_'+str(runlist[k])+'_CT5_CogMap')+'}',
                                          '\includegraphics[width=0.2\linewidth]{'+find_figure(available_figure, 'Run_'+str(runlist[k])+'_CT5_ShowerParticipation')+'}'])
            calibration_str += latex_table(calibration_table)
            calibration_str += '\n'
        report = report.replace('%calibration%', calibration_str)
        
        with open(join(report_folder, full_analysis_name + '.tex'), mode='w') as report_file:
            report_file.write(report)
            
        cwd = os.getcwd()
        os.chdir(report_folder)
        os.system('pdflatex -synctex=1 -interaction=nonstopmode ' + join(report_folder, full_analysis_name + '.tex'))
        os.chdir(cwd)
        
    if delete_tex_files:
        report_files = os.listdir(report_folder)
        for filename in report_files:
            if '.toc' in filename or '.synctex.gz' in filename or '.aux' in filename or '.log' in filename or '.tex' in filename:
                os.remove(join(report_folder, filename))
