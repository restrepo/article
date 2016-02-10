#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Module article: Fill article object from DOI
json: from DOI API
citations: from Google Scholar
Colciencias Info from ISSN or Journal name: depends on json
'''
import time
import requests
import pandas as pd
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.max_colwidth',500)
requests.packages.urllib3.disable_warnings()

def google_search(q='hello world'):
    '''
    From: http://stackoverflow.com/a/29292168
    '''
    rd={}
    link = 'http://ajax.googleapis.com/ajax/services/search/web?v=1.0&%s' %q
    ua = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_2)\
           AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.116 Safari/537.36'}                                                                
    payload = {'q': q}                                                                                                                                                                                   
    r = requests.get(link, headers=ua, params=payload)
    if r.status_code==200:
        rd=r.json()
    return rd
    
def ImpactFactor(issn='1539-3755'):
    ifdf=pd.DataFrame()
    q='site:www.bioxbio.com/if/ %s' %issn
    rd=google_search(q)
    
    IF=''
    if rd:
        if rd.has_key('responseData'): # if exits, is a dict
            if rd['responseData'].has_key('results'): 
                if len(rd['responseData']['results'])>0:
                    if rd['responseData']['results'][0].has_key('content'):
                        IF=rd['responseData']['results'][0]['content']
        
        if IF:
            IF=IF.replace('\n','').split('impact factors:')
            if len(IF)>0:
                IF=IF[1].split('. ISSN')[0].split(',') #always works for a string
                IF=[ify.replace(')','').split('(') for ify in  IF]
                if len(IF[0])==2:
                    ifdf=pd.DataFrame(IF,columns=['IF','Year'])
                    
    return ifdf

def keysdash2underscore(ds):
    '''
    Convert keys with dash  to keys with underscore
    '''
    dfk=pd.DataFrame(ds.keys(),columns=['keys'])
    for k in dfk[dfk['keys'].str.contains('[A-Za-z]+-[A-Za-z]')].values:
        ds[k[0].replace('-','_')]=ds[k[0]]
        
    return ds

class article(object):
    '''
    Obtain info from D0I
    '''
    article=pd.Series()
    article['citations']=pd.Series()
    journal=pd.Series() #self.article.journal.ranking.colciencias.issn
    journal['ranking']=pd.Series()
    journal.ranking['colciencias']=pd.Series()
    journal['Impact_Factor']=pd.Series()
    def __init__(self,doi='10.1007/JHEP11(2013)011',citations=False,metadata=True,colciencias=False,\
                 quartil=False,impact_factor=False,google_scholar_delay=2):
        urldoi='http://dx.doi.org/'
        if quartil or colciencias:
            ranking=True
        if impact_factor and not colciencias:
            metadata=True
            
        doi=doi.replace(urldoi,'')
        self.journal.ranking.colciencias['ISSN']=''
        
        if citations:
            ua = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_2)\
                AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.116 Safari/537.36'}       
            r=requests.get('https://scholar.google.com/scholar?q=%s' %doi,headers=ua,verify=False)
            time.sleep(google_scholar_delay)
            sep='">Cited by'
            self.article.citations['number']=''
            self.article.citations['url']=''
            self.article.citations['status']='OK'
            self.article.citations['html']=r.text
            if r.text.lower().find('captcha')!=-1:
                self.article.citations.status='CAPTCHA'
                print 'WARNING: Google Scholar bot protection actived. Citation search banned'
            if r.text.find(sep)!=-1:
                rr=r.text.split(sep)
                self.article.citations['number']=rr[1].split('</a>')[0].strip()
                self.article.citations['url']='https://scholar.google.com%s' %rr[0].split('<a href="')[-1]
                
        if metadata:    
            r=requests.get(urldoi+doi,\
                       headers ={'Accept': 'application/citeproc+json'})
            if r.status_code==200:
                self.article=self.article.append(pd.Series(r.json()))
                self.article=keysdash2underscore(self.article)
                for k in self.article.keys():
                    if type(self.article[k])==dict:
                        self.article[k]=pd.Series(self.article[k])
                        self.article[k]=keysdash2underscore(self.article[k])
                        
                    if type(self.article[k])==list:
                        if k=='funder' or k=='license' or k=='link' or k=='author':
                            if self.article[k]:
                                self.article[k]=pd.DataFrame(self.article[k])
        
                        if k=='subject' or k=='subtitle':
                            if self.article[k]:
                                self.article[k]=self.article[k][0]
                                

        #TODO: fill self.journal Series with relevant metadata: ['id','name','abbreviation','ISSN'], etc
        if not colciencias:
            if metadata:
                 self.journal.ranking.colciencias.ISSN=self.article.ISSN[0]
        #else: force issn colciencias
        if impact_factor:
            self.journal.Impact_Factor=ImpactFactor(self.journal.ranking.colciencias.ISSN)
if __name__ == "__main__":                
    a=article(doi='http://dx.doi.org/10.1103/PhysRevD.92.013005',citations=True)
    print a.article.citations.number
    print a.article.author
