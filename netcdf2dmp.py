# -*- coding: utf-8 -*-
"""
Created on Thu Jan  3 14:18:10 2019

@author: Robert Huber
"""
import xarray as xr
import os
import re
import sys
import uuid
import pandas as pd
import traceback
#ds=xr.open_dataset(folder+'\\EuroSITES_19_OS_PAP-1_201009_R_PCO2.nc')

#print(len(os.listdir(ncfolder)))
#986

class Parameter:
     def __init__(self, name='', unit='',uri='',label=''):
        self.name=name
        self.unit=unit
        self.uri=uri
        self.label=label
        self.longname=label+' ('+name+')'

class Sensor:
    def __init__(self, id, name=''):
        self.id=id
        self.name=name
        self.outputs=[]
        self.feature=''
        self.lat=0
        self.lon=0
        
    def getParameters(self):
        for out in self.outputs:
            print(out.name)
        
    def addParameter(self,name, unit='1',uri='', label=''):
        self.outputs.append(Parameter(name, unit,uri, label))
    
    def setPosition(self,lat,lon, depth):
        self.lat=lat
        self.lon=lon
        self.depth=depth
    

class EMSO2DMP:
    def __init__(self, site='',platform=''):
        self.dataTypeNames=['Unknown','Time series','Depth profile','Time series profile']
        self.type=0
        self.defaultSensor='unknown_sensor'
        self.site=site
        self.lat=0
        self.lon=0
        self.sensors=dict()
        self.platform=platform
        self.deployment=''
        self.startDate='0000-00-00'
        self.id=''
        
        self.variables=dict()
        df = pd.read_excel('param.xlsx')
        for index, row in df.iterrows():
            if row['source']=='cf':
                uri='http://mmisw.org/ont/cf/parameter/'+row['long_name']
            elif row['source']=='ioos':
                uri='http://mmisw.org/ont/ioos/OA/'+row['long_name']
            elif row['source']=='p09':
                uri='http://vocab.nerc.ac.uk/collection/P09/current/'+row['long_name']
            else:
                 uri='emso.eu/variables/'+row['long_name']
            self.variables[str.upper(row['code'])]={'long_name':row['long_name'],'uri':uri}
        #print(self.variables)

    
    def createSensorML(self, sensor):
        xml=''
        #for sensor in self.sensors.values():
            #xml+='<?xml version="1.0" encoding="UTF-8"?>'
        xml+='<sml:PhysicalSystem gml:id="s_'+str(sensor.id)+'_at_'+self.platform+'">'
        xml+='<gml:identifier codeSpace="uniqueID">s_'+str(sensor.id)+'</gml:identifier>'
        xml+='<sml:identification><sml:IdentifierList>'
        xml+='<sml:identifier><sml:Term definition="http://vocab.ndg.nerc.ac.uk/term/W07/current/IDEN0002"><sml:label>longName</sml:label><sml:value>'+sensor.name+'</sml:value></sml:Term></sml:identifier>'
        xml+='<sml:identifier><sml:Term definition="http://vocab.ndg.nerc.ac.uk/term/W07/current/IDEN0006"><sml:label>shortName</sml:label><sml:value>'+sensor.name+'</sml:value></sml:Term></sml:identifier>'
        xml+='<sml:identifier><sml:Term definition="http://vocab.ndg.nerc.ac.uk/term/W07/current/IDEN0007"><sml:label>UUID</sml:label><sml:value>s_'+str(sensor.id)+'</sml:value></sml:Term></sml:identifier>'
        xml+='</sml:IdentifierList></sml:identification>'
        xml+='<sml:capabilities name="offerings"><sml:CapabilityList><sml:capability name="offeringID"><swe:Text definition="urn:ogc:def:identifier:OGC:offeringID"><swe:label>s_'+str(sensor.id)+' Offerings</swe:label>'
        xml+='<swe:value>offering_s_'+str(sensor.id)+'</swe:value></swe:Text></sml:capability></sml:CapabilityList></sml:capabilities>'
            #xml+='<sml:featuresOfInterest><sml:FeatureList definition="http://www.opengis.net/def/featureOfInterest/identifier"><swe:label>featuresOfInterest</swe:label><sml:feature xlink:href="http://www.emso.eu/sites/'+self.site+'"/></sml:FeatureList></sml:featuresOfInterest>'
        xml+='<sml:outputs><sml:OutputList>'
        for param in sensor.outputs:
            xml+='<sml:output name="'+param.label+'">'
            xml+='<swe:Quantity definition="'+param.uri+'">'
            xml+='<swe:identifier>'+param.name+'</swe:identifier>'
            xml+='<swe:label>'+str(param.label).replace('_',' ')+'</swe:label>'
            xml+='<swe:description>'+param.longname+'</swe:description>'
            xml+='<swe:uom code="'+param.unit+'"/>'
            xml+='</swe:Quantity>'
            xml+='</sml:output>'            
        xml+='</sml:OutputList></sml:outputs>'
        xml+='<sml:attachedTo xlink:href="http://emso.eu/platform/'+self.platform+'" xlink:title="emso.eu:deployment:'+self.platform+':'+self.site+':'+self.startDate[:10]+'"/>'
        xml+='<sml:position><swe:Vector referenceFrame="urn:ogc:def:crs:EPSG::4326">'
        xml+='<swe:coordinate name="easting"><swe:Quantity axisID="x"><swe:uom code="degree"/><swe:value>'+str(sensor.lat)+'</swe:value></swe:Quantity></swe:coordinate>'
        xml+='<swe:coordinate name="northing"><swe:Quantity axisID="y"><swe:uom code="degree"/><swe:value>'+str(sensor.lon)+'</swe:value></swe:Quantity></swe:coordinate>'
        xml+='<swe:coordinate name="altitude"><swe:Quantity axisID="z"><swe:uom code="m"/><swe:value>'+str(sensor.depth)+'</swe:value></swe:Quantity></swe:coordinate>'
        xml+='</swe:Vector></sml:position>'
        xml+='</sml:PhysicalSystem>'
        return xml
    
    def createInsertSensorXML(self, sensor):
        xml=''
        xml+='<swes:InsertSensor service="SOS" version="2.0.0" xmlns:swes="http://www.opengis.net/swes/2.0" xmlns:sos="http://www.opengis.net/sos/2.0" xmlns:swe="http://www.opengis.net/swe/2.0" '
        xml+='xmlns:sml="http://www.opengis.net/sensorml/2.0" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        xml+='xmlns:gco="http://www.isotc211.org/2005/gco" xmlns:gmd="http://www.isotc211.org/2005/gmd" xsi:schemaLocation="http://www.opengis.net/sos/2.0 http://schemas.opengis.net/sos/2.0/sosInsertSensor.xsd   http://www.opengis.net/swes/2.0 http://schemas.opengis.net/swes/2.0/swes.xsd">'
        xml+='<swes:procedureDescriptionFormat>http://www.opengis.net/sensorml/2.0</swes:procedureDescriptionFormat>'
        xml+='<swes:procedureDescription>'
        xml+=self.createSensorML(sensor)
        xml+='</swes:procedureDescription>'
        for param in sensor.outputs:
            xml+='<swes:observableProperty>'+param.uri+'</swes:observableProperty>'
        xml+='<swes:metadata><sos:SosInsertionMetadata>'
        xml+='<sos:observationType>http://www.opengis.net/def/observationType/OGC-OM/2.0/OM_Measurement</sos:observationType>'
        xml+='<sos:observationType>http://www.opengis.net/def/observationType/OGC-OM/2.0/OM_ComplexObservation</sos:observationType>'
        xml+='<sos:observationType>http://www.opengis.net/def/observationType/OGC-OM/2.0/OM_CategoryObservation</sos:observationType>'
        xml+='<sos:observationType>http://www.opengis.net/def/observationType/OGC-OM/2.0/OM_CountObservation</sos:observationType>'
        xml+='<sos:observationType>http://www.opengis.net/def/observationType/OGC-OM/2.0/OM_TextObservation</sos:observationType>'
        xml+='<sos:observationType>http://www.opengis.net/def/observationType/OGC-OM/2.0/OM_TruthObservation</sos:observationType>'
        xml+='<sos:observationType>http://www.opengis.net/def/observationType/OGC-OM/2.0/OM_GeometryObservation</sos:observationType>'
        xml+='<sos:observationType>http://www.opengis.net/def/observationType/OGC-OM/2.0/OM_ComplexObservation</sos:observationType>'
        xml+='<sos:observationType>http://www.opengis.net/def/observationType/OGC-OM/2.0/OM_SWEArrayObservation</sos:observationType>'
        xml+='<sos:featureOfInterestType>http://www.opengis.net/def/samplingFeatureType/OGC-OM/2.0/SF_SamplingPoint</sos:featureOfInterestType>'
        xml+='</sos:SosInsertionMetadata></swes:metadata>'
        xml+='</swes:InsertSensor>'
        xml+="\n\n"
        return xml
        
    def createInsertResultTemplateXML(self,sensor):
        xml='<sos:InsertResultTemplate service="SOS" version="2.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:swes="http://www.opengis.net/swes/2.0" xmlns:sos="http://www.opengis.net/sos/2.0" '
        xml+='xmlns:swe="http://www.opengis.net/swe/2.0" xmlns:sml="http://www.opengis.net/sensorML/1.0.1" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xlink="http://www.w3.org/1999/xlink" '
        xml+='xmlns:om="http://www.opengis.net/om/2.0" xmlns:sams="http://www.opengis.net/samplingSpatial/2.0" xmlns:sf="http://www.opengis.net/sampling/2.0" xmlns:xs="http://www.w3.org/2001/XMLSchema" xsi:schemaLocation="http://www.opengis.net/sos/2.0 http://schemas.opengis.net/sos/2.0/sosInsertResultTemplate.xsd http://www.opengis.net/om/2.0 http://schemas.opengis.net/om/2.0/observation.xsd  http://www.opengis.net/samplingSpatial/2.0 http://schemas.opengis.net/samplingSpatial/2.0/spatialSamplingFeature.xsd">'
        xml+='<sos:proposedTemplate><sos:ResultTemplate>'
        xml+='<swes:identifier>s_'+str(sensor.id)+'_'+self.site+'_'+self.startDate[:10]+'</swes:identifier>'
        xml+='<swes:extension>'
        xml+='<sml:attachedTo xlink:href="http://emso.eu/platform/'+self.platform+'" xlink:title="emso.eu:deployment:'+self.platform+':'+self.site+':'+self.startDate[:10]+'"/>'
        xml+='</swes:extension>'
        xml+='<sos:offering>offering_s_'+str(sensor.id)+'</sos:offering>'
        xml+='<sos:observationTemplate><om:OM_Observation gml:id="sensor2obsTemplate"><om:type xlink:href="http://www.opengis.net/def/observationType/OGC-OM/2.0/OM_ComplexObservation"/><om:phenomenonTime nilReason="template"/><om:resultTime nilReason="template"/>'
        xml+='<om:procedure xlink:href="s_'+str(sensor.id)+'"/>'
        xml+='<om:observedProperty xlink:href="s_'+str(sensor.id)+'_observations"/>'
        xml+='<om:featureOfInterest><sams:SF_SpatialSamplingFeature gml:id="'+self.site+'">'
        xml+='<gml:identifier codeSpace="EMSO">http://www.emso.eu/site/'+self.site+'</gml:identifier><gml:name>'+self.site+'</gml:name>'
        xml+='<sf:type xlink:href="http://www.opengis.net/def/samplingFeatureType/OGC-OM/2.0/SF_SamplingPoint"/><sf:sampledFeature xlink:href="http://www.opengis.net/def/nil/OGC/0/unknown"/>'
        xml+='<sams:shape><gml:Point gml:id="'+self.site+'_coordinates"><gml:pos srsName="http://www.opengis.net/def/crs/EPSG/0/4326">'+self.lat+' '+self.lon+'</gml:pos></gml:Point></sams:shape>'
        xml+='</sams:SF_SpatialSamplingFeature></om:featureOfInterest>'
        xml+='<om:result/></om:OM_Observation></sos:observationTemplate>'
        xml+='<sos:resultStructure><swe:DataRecord>'
        xml+='<swe:field name="phenomenonTime"><swe:Time definition="http://www.opengis.net/def/property/OGC/0/PhenomenonTime"><swe:uom xlink:href="http://www.opengis.net/def/uom/ISO-8601/0/Gregorian"/></swe:Time></swe:field>'
        xml+='<swe:field name="s_'+str(sensor.id)+'_data_container"><swe:DataRecord definition="s_'+str(sensor.id)+'_observations">'
    
        for param in sensor.outputs:
            xml+='<swe:field name="'+param.label+'">'
            xml+='<swe:Quantity definition="'+param.uri+'">'
            xml+='<swe:identifier>'+param.name+'</swe:identifier>'
            xml+='<swe:label>'+str(param.label).replace('_',' ')+'</swe:label>'
            xml+='<swe:description>'+param.longname+'</swe:description>'
            xml+='<swe:uom code="'+param.unit+'"/>'
            xml+='</swe:Quantity>'
            xml+='</swe:field>'
        xml+='</swe:DataRecord></swe:field></swe:DataRecord></sos:resultStructure>'
        xml+=' <sos:resultEncoding><swe:TextEncoding tokenSeparator="#" blockSeparator="@"/></sos:resultEncoding>'
        xml+='</sos:ResultTemplate></sos:proposedTemplate></sos:InsertResultTemplate>'
        return xml
    
    def createInsertResultXML(self, sensor):
        xml='<sos:InsertResult xmlns:sos="http://www.opengis.net/sos/2.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" service="SOS" version="2.0.0" xsi:schemaLocation="http://www.opengis.net/sos/2.0 http://schemas.opengis.net/sos/2.0/sos.xsd">'
        xml+='<sos:template>s_'+str(sensor.id)+'_'+self.site+'_'+self.startDate[:10]+'</sos:template>'
        xml+='<sos:resultValues>'+self.getSensorDataAsASCII(sensor)+'</sos:resultValues>'
        xml+='</sos:InsertResult>'
        return xml
        
    def open(self, file, clean=True):
        if file.endswith(".nc"):
            #print(file)
            self.uuid=uuid.uuid3(uuid.NAMESPACE_DNS,file)
            try:
                self.xrds=xr.open_dataset(file)  
                if self.site=='':
                    self.site=self.xrds.attrs.get('site_code','')
                if self.platform=='':
                    self.platform=self.xrds.attrs.get('platform_code','')
                self.startDate=self.xrds.attrs.get('time_coverage_start','')
                self.lat=self.xrds.attrs.get('geospatial_lat_min',0)

                self.lon=self.xrds.attrs.get('geospatial_lon_min',0)
                self.deployment=str('emso.eu:deployment:'+self.platform+'@'+self.site+':'+self.startDate[:10])
                self.id=hash(file)
                
                #print(self.xrds)
                if clean==True:
                    dropcandidates = ['POSITIONING_SYSTEM','DC_REFERENCE','TEMPQC','DATA_MODE','DATA_MODE_CORA','NUM_PROFILE','PCO2QC','PHQC','PSAL_101QC','STATION_NAME','STA_NUMBER','TIME_BOUNDS','DIRECTION','CAST_NUMBER','POSITION']
                    vars2drop=[]
                    for k in self.xrds.variables.keys():
                        if re.search(r'_(DM|QC|ANCILLARY|STD)\Z',k, re.IGNORECASE):
                            vars2drop.append(k)
                                
                    for k in dropcandidates:
                        if k in self.xrds.variables:
                            vars2drop.append(k)
                    self.xrds=self.xrds.drop(vars2drop)  
               # print(self.xrds.attrs)
                #print(self.xrds.dims)
                self.setType()
                #print(self.xrds['DEPTH'].values)
                for depth in self.xrds['DEPTH'].values:
                    for var in self.xrds.variables:                        
                        if var not in self.xrds.dims:
                            sensorName=self.xrds.variables[var].attrs.get('sensor_name', self.defaultSensor)+'_at_'+str(depth)+'m'                        
                            unit=self.xrds.variables[var].attrs.get('units', '1')
                            var=str.upper(var)
                            if sensorName not in self.sensors:
                                sensorID=uuid.uuid3(uuid.NAMESPACE_DNS,sensorName)
                                sensor=Sensor(sensorID,sensorName)
                                sensor.setPosition(self.lat, self.lon, depth)
                                self.sensors[sensorName]=sensor
                                self.sensors[sensorName].addParameter(var,unit, self.variables[var]['uri'],self.variables[var]['long_name'])
                            else:
                                self.sensors[sensorName].addParameter(var,unit,self.variables[var]['uri'],self.variables[var]['long_name'])
                           
                            #print(self.xrds.variables[var].attrs)
                            #print(var+' - '+sensorName+' - '+unit)
            except Exception as e:
                print ('ERROR:  '+str(e))
                tb = traceback.format_exc()
            else:
                tb = "No error"
            finally:
                print(tb)
                
    def getSensorDataAsASCII(self, sensor):      
        df=self.xrds.to_dataframe()
        df=df.reset_index()
        df=df[(df['DEPTH']==sensor.depth)]
        df=df.drop(['DEPTH','LATITUDE','LONGITUDE'], axis=1)
        return df.to_csv(header=False,index=False,sep='#', line_terminator='@',date_format='%Y-%m-%dT%H:%M:%S')
                
    def setType(self):
        x=y=z=t=0
        x=self.xrds.dims.get('LATITUDE',0)
        y=self.xrds.dims.get('LONGITUDE',0)
        t=self.xrds.dims.get('TIME',0)
        z=self.xrds.dims.get('DEPTH',0)        
        if x==1 and y==1:
            if t>=1 and z==1:
                self.type=1
            elif t==1 and z>=1:
                self.type=2
            elif t>=1 and z>=1 and t>z:
                self.type=3                
        return self.dataTypeNames[self.type]
'''
allvars=[]
#ncfolder='C:\\Users\\Robert\\workspace\\fixo3_nc2md\\cache\\'
ncfolder='C:\\Users\\Robert Huber\\Dropbox\\netcdfexport\\NetCDF-Metadata\cache\\'

#file='EuroSITES_10_OS_ANTARES_2010_R_CTD.nc'
#file='EuroSITES_19_OS_PAP-1_201009_R_PCO2.nc'
#file='MO_PR_BO_E1M3A_2012.nc'
#file='PLOCAN_11_OS_ESTOC-1_200901_D_CTD.nc'
file='OS_PAP-2_200210_D_CTD.nc'
#file='OS_ANTARES-1_200901_D_CTD.nc'
savedir=file.replace('.nc','')
print(savedir)
try:
    os.mkdir(savedir)
except Exception as e:
    print(e)
ds= EMSO2DMP()
ds.open(ncfolder+file)
print(ds.dataTypeNames[ds.type])
print(ds.site)
print(ds.platform)
print(ds.deployment)
'''
#if len(ds.sensors)>0:
#    sensor=next(iter(ds.sensors.values()))
#    print(sensor.name)
#sensor.getParameters()
'''
for sensor in ds.sensors.values():
    templatexml=ds.createInsertResultTemplateXML(sensor)
    sensorxml=ds.createInsertSensorXML(sensor)
    resultxml=ds.createInsertResultXML(sensor)
    sxf=open(savedir+"\\insertSensor_"+str(sensor.id)+'.xml', "w")
    txf = open(savedir+"\\insertresultTemplate_"+str(sensor.id)+'.xml', "w")
    rxf = open(savedir+"\\insertResult_"+str(sensor.id)+'.xml', "w")
    txf.write(templatexml)
    sxf.write(sensorxml)
    rxf.write(resultxml)
    sxf.close()
    txf.close()
    rxf.close()
'''
#print(ds.createInsertResultTemplateXML(sensor))

#ds.getSensorDataAsASCII(sensor)
#for file in os.listdir(ncfolder):

'''   
print(allvars.sort())
print(len(allvars))

for av in allvars:
    print(av)
'''

'''

#print(ds)
if 'DEPH' in ds.variables:    
    if len(ds['DEPH'].shape)>1:
        ds['DEPTH']=ds['DEPH'][0]
        print (ds['DEPTH'])

#print(ds)
#ds=ds.set_coords(['DEPTH'])

try:
    pd=ds.to_dataframe()
    print(pd.head(10))
except:
    print('Error')
'''