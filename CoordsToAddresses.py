import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon, Point
from shapely import wkt
import numpy as np
import random
import matplotlib.pyplot as plt
import math
import urllib.request
import json
import time


zipcode_shape_file = r"C:\Users\27761\Desktop\Research\Address-Coordinates\zcta_shape_file.csv"
coords_in_zip_code = r"C:\Users\27761\Desktop\Research\Address-Coordinates\coords_result_final.csv"
address_in_zip_code = r"C:\Users\27761\Desktop\Research\Address-Coordinates\address_result_final.csv"
nominatim_baseurl =r"https://nominatim.openstreetmap.org/"
number_of_random_points = 10
tries_per_address = 20


def random_points_in_polygon(number, polygon):
    points = []
    display_names =[]
    min_x, min_y, max_x, max_y = polygon.bounds
    i= 0
    tries = 0
    while i < number:
        tries = tries +1
        if (tries > number_of_random_points * tries_per_address):
            break

        point = Point(random.uniform(min_x, max_x), random.uniform(min_y, max_y))
        lat = point.y
        lon = point.x
        jsonout = get_address_json(lat,lon)

        if polygon.contains(point) and is_house(jsonout):
            points.append(point)
            display_names.append(json.dumps(jsonout))
            i += 1
    print("tried: " +str(tries))
    return points,display_names  # returns list of shapely point

def get_coords_tuple_string(random_points):
    results = ""
    for i in range(len(random_points)):
        results = results + str(random_points[i].y) + " "
        results = results + str(random_points[i].x)
        if (i != len(random_points) -1):
            results = results + "|"
    return results

def get_address_tuple_string(addresses):
    results = ""
    for i in range(len(addresses)):
        results = results + addresses[i]
        if (i != len(addresses) -1):
            results = results + "|"
    return results


def append_coords_to_file(zipcodes,random_points,write_header,fileout):
        df = pd.DataFrame(list(zip(zipcodes,random_points)), columns=["zipcode", "coordinates"])
        df.to_csv(fileout, mode='a', index=False, header =write_header )

def append_address_to_file(zipcodes,addresses,write_header,fileout):
        df = pd.DataFrame(list(zip(zipcodes,addresses)), columns=["zipcode", "addresses"])
        df.to_csv(fileout, mode='a', index=False, header =write_header )

def get_addresses():
    df = pd.read_csv(coords_in_zip_code,nrows= 1)
    for i in range(len(df.index)):
        geocodes = df["coordinates"].apply(str)[0].split(",")

        for j in range(len(geocodes)):   
            lat = geocodes[j].split(" ")[0]
            lon = geocodes[j].split(" ")[1]
            get_address_json(lat,lon)

def is_house(json):
    return json["type"] == "house"

def get_address_json(lat,lon):
    t0 = time.time()
    req = urllib.request.urlopen(nominatim_baseurl + "reverse?format={}&lat={}&lon={}&zoom={}".format("jsonv2", lat,lon, 18))
    contents = req.read().decode('utf-8')
    output = json.loads(contents)
    t1 = time.time()
    diff = t1-t0
    #print("elapsed in ms:" + str(t1-t0))

    if (diff < 1):
    #    print("sleep for:" + str(diff+0.1))
        time.sleep(diff+0.1)
    print(output["type"])

    return output


def get_interested_coords_and_address(last_read_line = 1):

    df = pd.read_csv(zipcode_shape_file)
    size = len(df.index)
    writer_header = False

    for j in range(math.ceil(size/100)):

        print("reading shape file")
        df = pd.read_csv(zipcode_shape_file, nrows=100,skiprows= j*100+last_read_line, names=["ZCTA5CE10","GEOID10","CLASSFP10","MTFCC10","FUNCSTAT10","ALAND10","AWATER10","INTPTLAT10","INTPTLON10","geometry"])

        print("reading done and now parse geometry column...")
        df['geometry'] = df['geometry'].apply(wkt.loads)
        gdf_polys = gpd.GeoDataFrame(df,geometry = 'geometry')
        print("parse is done")

        for i in range(len(gdf_polys.index)):
            if (i == 0 and j == 0 and last_read_line == 1):
                writer_header = True
            else:
                writer_header = False

            zipcodes =[]
            coordinates_str =[]
            displaynames_str =[]
            zone = gdf_polys.iloc[i]
            x_min, y_min, x_max, y_max = gdf_polys.total_bounds
            random_points, displaynames = random_points_in_polygon(number_of_random_points,gdf_polys.iloc[i].geometry)
            #xs = [point.x for point in random_points]
            #ys = [point.y for point in random_points]
            zipcodes.append(zone.ZCTA5CE10)
            coordinates_str.append(get_coords_tuple_string(random_points))
            displaynames_str.append(get_address_tuple_string(displaynames))
            print("Processed row number: " + str(i))
            append_coords_to_file(zipcodes, coordinates_str,writer_header,coords_in_zip_code)
            append_address_to_file(zipcodes,displaynames_str,writer_header, address_in_zip_code )

get_interested_coords_and_address()
#get_addresses()
#print(processed_geomtry_str)







