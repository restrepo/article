#!/usr/bin/env python
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
    urldoi='http://dx.doi.org/'
    citedby=pd.Series()
    json=pd.Series()
    def __init__(self,doi='10.1007/JHEP11(2013)011',citations=False,json=True,colciencias=False,\
                 impact_factor=True):
        if impact_factor and not colciencias:
            json=True
            
        self.doi=doi.replace(self.urldoi,'')
        self.issn=''
        #print 'TODO: JSON metadata here'
        
        if citations:
            r=requests.get('https://scholar.google.com/scholar?q=%s' %self.urldoi+self.doi,verify=False)
            time.sleep(60)
            sep='">Cited by'
            self.citedby['number']='';self.citedby['url']='';self.status='OK'
            if r.text.find('CAPTCHA')!=-1:
                self.status='CAPTCHA'
            if r.text.find(sep)!=-1:
                rr=r.text.split(sep)
                self.citedby['number']=rr[1].split('</a>')[0].strip()
                self.citedby['url']='https://scholar.google.com%s' %rr[0].split('<a href="')[-1]
                
        if json:    
            r=requests.get(self.urldoi+self.doi,\
                       headers ={'Accept': 'application/citeproc+json'})
            if r.status_code==200:
                self.json=pd.Series(r.json())
                self.json=keysdash2underscore(self.json)
                for k in self.json.keys():
                    if type(self.json[k])==dict:
                        self.json[k]=pd.Series(self.json[k])
                        self.json[k]=keysdash2underscore(self.json[k])
                        
                    if type(self.json[k])==list:
                        if k=='author' or k=='funder' or k=='license' or k=='link':
                            if self.json[k]:
                                self.json[k]=pd.DataFrame(self.json[k])
                        if k=='subject' or k=='subtitle':
                            if self.json[k]:
                                self.json[k]=self.json[k][0]
                #proper sub-Series for nested json keys...
        if not colciencias:
            if json:
                self.issn=self.json.ISSN[0]
        #else: force issn colciencias
        if impact_factor:
            self.impact_factor=ImpactFactor(self.issn)
if __name__ == "__main__":                
    a=article(doi='http://dx.doi.org/10.1103/PhysRevD.92.013005',citations=True)
    print a.citedby.number
    print a.json.author.to_string
