import json

import pandas as pd
from flask import Flask, render_template
from flask import request

from climbing_routes_info import list_steepness, list_styles
from grades_info import dic_grades_reverse_GUI, dic_grades_GUI

application = Flask(__name__)

crags = pd.read_csv('db/crags_Arco_v2.csv', header=0,
                    names=['name', 'lat', 'long', 'vllocationid', 'cragSlug', 'ascents', 'routes'])
users_profiles = pd.read_csv('./db/users_Arco_v4.csv')
sporclimbing_routes = pd.read_csv('./db/Arco_routes_v6.csv')

password = 'admin'

markers = []
for ind in crags.index:
    marker = {
        'lat': crags.loc[ind, 'lat'],
        'lon': crags.loc[ind, 'long'],
        'name': crags.loc[ind, 'name'],
        'cragSlug': crags.loc[ind, 'cragSlug'],
        'ascents': crags.loc[ind, 'ascents'],
        'routes': crags.loc[ind, 'routes'],
    }
    markers.append(marker)


def find_recommendations_for_crags(checked_styles, checked_styles_least, checked_steepness, checked_grades,
                                   type_recommendation):
    res_crags = {}
    flag_cold_start = False
    number_crags = 0
    for ind in crags.index:
        cragSlug = crags.loc[ind, 'cragSlug']
        num_routes_in_crag = 0
        ds_current_routes = sporclimbing_routes[sporclimbing_routes.cragSlug == cragSlug]
        result = ds_current_routes.to_json(orient="records")
        parsed = json.loads(result)

        if type_recommendation == 'favourite':
            styles_to_compare = checked_styles
        else:
            styles_to_compare = checked_styles_least

        for points in parsed:
            flag_style, flag_steepness, flag_grade = False, False, False
            grade_name = 'vl-' + str(points['gradeIndex'])
            if (dic_grades_reverse_GUI[grade_name] in checked_grades.keys()) or (len(checked_grades.keys()) == 0):
                flag_grade = True
            for each_style in list_styles:
                if (points[each_style] == 1 and each_style in styles_to_compare.keys()) or (
                        len(styles_to_compare.keys()) == 0):
                    flag_style = True
            for each_steepness in list_steepness:
                if points[each_steepness] == 1 and each_steepness in checked_steepness.keys() or (
                        len(checked_steepness.keys()) == 0):
                    flag_steepness = True
            if flag_grade and flag_style and flag_steepness:
                num_routes_in_crag += 1
        if num_routes_in_crag > 0:
            number_crags += 1
            res_crags[cragSlug] = num_routes_in_crag
    if number_crags == 0:
        flag_cold_start = True
        # recommend top-10
        i = 0
        for ind in crags.sort_values(by='routes', ascending=False).index:
            cragSlug = crags.loc[ind, 'cragSlug']
            num_routes_in_crag = crags.loc[ind, 'ascents']
            res_crags[cragSlug] = num_routes_in_crag
            i += 1
            if i > 10:
                break
    sorted_list_of_crags = [key for key, _ in sorted(res_crags.items(), key=lambda x: x[1], reverse=True)]

    if len(sorted_list_of_crags) > 10:
        sorted_list_of_crags = sorted_list_of_crags[:10]
    return res_crags, sorted_list_of_crags, flag_cold_start


def load_preferences_from_get_request(user_id, args):
    checked_styles = {}
    checked_styles_least = {}
    dic_preferences = {'user_id': user_id}
    for each_style in list_styles:
        dic_preferences[each_style] = 0
        dic_preferences[each_style + '_least'] = 0
        if args.get(each_style) == 'on':
            checked_styles[each_style] = 1
            dic_preferences[each_style] = 1
        if args.get(each_style + '_least') == 'on':
            checked_styles_least[each_style] = 1
            dic_preferences[each_style + '_least'] = 1
    checked_steepness = {}
    for each_steepness in list_steepness:
        dic_preferences[each_steepness] = 0
        if args.get(each_steepness) == 'on':
            checked_steepness[each_steepness] = 1
            dic_preferences[each_steepness] = 1
    checked_grades = {}
    dic_preferences['checked_grades'] = {}
    for each_key in dic_grades_GUI.keys():
        dic_preferences['checked_grades'][each_key] = 0
        if args.get(each_key) == 'on':
            checked_grades[each_key] = 1
            dic_preferences['checked_grades'][each_key] = 1
    type_recommendation = args.get('type_recommendation')
    dic_preferences['type_recommendation'] = type_recommendation
    return dic_preferences, checked_styles, checked_styles_least, checked_steepness, checked_grades


def render_refresh_page(user_id, user_data):
    checked_grades = {}
    for each_key in dic_grades_GUI.keys():
        checked_grades[each_key] = 0
    for each_grade in dic_grades_reverse_GUI.keys():
        if user_data[each_grade].values[0] > 0:
            checked_grades[dic_grades_reverse_GUI[each_grade]] = 1
    settings_dic = {
        'user_id': user_id,
        'athletic': user_data.athletic.values[0],
        'cruxy': user_data.cruxy.values[0],
        'endurance': user_data.endurance.values[0],
        'crimpy': user_data.fingerstrength.values[0],
        'sloper': user_data.sloppers.values[0],
        'technical': user_data.technical.values[0],
        'athletic_least': user_data.athletic_least.values[0],
        'cruxy_least': user_data.cruxy_least.values[0],
        'endurance_least': user_data.endurance_least.values[0],
        'crimpy_least': user_data.fingerstrength_least.values[0],
        'sloper_least': user_data.sloppers_least.values[0],
        'technical_least': user_data.technical_least.values[0],
        'vertical': user_data.vertical.values[0],
        'overhang': user_data.overhang.values[0],
        'roof': user_data.roof.values[0],
        'slab': user_data.slab.values[0],
        'checked_grades': checked_grades
    }
    return settings_dic


def render_refresh_route(args):
    user_id = int(args.get('user_id'))
    dic_preferences, checked_styles, checked_styles_least, checked_steepness, checked_grades = load_preferences_from_get_request(
        user_id, args)
    cragSlug = args.get('cragSlug')
    cragName = args.get('cragName')
    ds_current_routes = sporclimbing_routes[sporclimbing_routes.cragSlug == cragSlug]
    result = ds_current_routes.to_json(orient="records")
    parsed = json.loads(result)
    routes = {}
    for points in parsed:
        if points['sectorSlug'] not in routes.keys():
            routes[points['sectorSlug']] = [points]
        else:
            routes[points['sectorSlug']].append(points)

    return render_template('routes.html', data=dic_preferences,
                           routes=routes,
                           cragSlug=cragSlug,
                           cragName=cragName)


@application.route('/index', methods=('GET', 'POST'))
def root():
    args = request.args
    user_id = int(args.get('user_id'))
    user_data = users_profiles[users_profiles['user_id'] == user_id]
    if len(user_data) > 0:
        user_data = users_profiles[users_profiles['user_id'] == user_id]
        if len(user_data) > 0:
            settings_dic = render_refresh_page(user_id, user_data)
            return render_template('index.html',
                                   markers=markers,
                                   data=settings_dic)


@application.route('/routes', methods=('GET', 'POST'))
def routes():
    args = request.args
    return render_refresh_route(args)


@application.route('/recommended_routes', methods=('GET', 'POST'))
def recommended_routes():
    args = request.args
    if args.get('action') == 'refresh':
        return render_refresh_route(args)
    user_id = int(args.get('user_id'))
    cragSlug = args.get('cragSlug')
    cragName = args.get('cragName')
    ds_current_routes = sporclimbing_routes[sporclimbing_routes.cragSlug == cragSlug]
    result = ds_current_routes.to_json(orient="records")
    parsed = json.loads(result)

    dic_preferences, checked_styles, checked_styles_least, checked_steepness, checked_grades = load_preferences_from_get_request(
        user_id, args)
    if dic_preferences['type_recommendation'] == 'training':
        styles_to_compare = checked_styles_least
    else:
        styles_to_compare = checked_styles

    routes = {}
    for points in parsed:
        flag_style, flag_steepness, flag_grade = False, False, False
        grade_name = 'vl-' + str(points['gradeIndex'])
        if (dic_preferences['type_recommendation'] == 'motivation') and (
                (dic_grades_reverse_GUI[grade_name] in checked_grades.keys()) or (
                len(checked_grades.keys()) == 0)) and (points['dev'] <= -1):
            flag_grade = True
        elif ((dic_preferences['type_recommendation'] == 'training') or (
                dic_preferences['type_recommendation'] == 'favourite')) and (
                dic_grades_reverse_GUI[grade_name] in checked_grades.keys()) or (len(checked_grades.keys()) == 0):
            flag_grade = True
        for each_style in list_styles:
            if (points[each_style] == 1 and each_style in styles_to_compare.keys()) or (
                    len(styles_to_compare.keys()) == 0):
                flag_style = True
        for each_steepness in list_steepness:
            if points[each_steepness] == 1 and each_steepness in checked_steepness.keys() or (
                    len(checked_steepness.keys()) == 0):
                flag_steepness = True
        if flag_grade and flag_style and flag_steepness:
            # add to the dictionary
            if points['sectorSlug'] not in routes.keys():
                routes[points['sectorSlug']] = [points]
            else:
                routes[points['sectorSlug']].append(points)

    return render_template('routes.html', data=dic_preferences,
                           routes=routes,
                           cragSlug=cragSlug,
                           cragName=cragName)


@application.route("/login", methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        user_id_entered = int(request.form['username'])
        password_entered = request.form['password']
        user_data = users_profiles[users_profiles['user_id'] == user_id_entered]
        if len(user_data) > 0 and password_entered == password:
            user_data = users_profiles[users_profiles['user_id'] == user_id_entered]
            if len(user_data) > 0:
                settings_dic = render_refresh_page(user_id_entered, user_data)
                return render_template('index.html',
                                       markers=markers,
                                       data=settings_dic)

        else:
            error = 'There is no user with this id, or the wrong password. Please try again.'
            return render_template('login.html', error=error)
    else:
        return render_template('login.html', error='')


@application.route("/temp", methods=('GET', 'POST'))
def temp():
    return render_template('temp.html', error='')


@application.route("/recommended_crags", methods=('GET', 'POST'))
def recommended_crags():
    args = request.args
    user_id_entered = int(args.get('user_id'))
    if args.get('action') == 'refresh':
        user_data = users_profiles[users_profiles['user_id'] == user_id_entered]
        if len(user_data) > 0:
            settings_dic = render_refresh_page(user_id_entered, user_data)
            return render_template('index.html',
                                   markers=markers,
                                   data=settings_dic)
    dic_preferences, checked_styles, checked_styles_least, checked_steepness, checked_grades = load_preferences_from_get_request(
        user_id_entered, args)
    recommended_crags, sorted_list_of_crags, flag_cold_start = find_recommendations_for_crags(checked_styles,
                                                                                              checked_styles_least,
                                                                                              checked_steepness,
                                                                                              checked_grades,
                                                                                              dic_preferences[
                                                                                                  'type_recommendation'])
    max_routes_num = recommended_crags[sorted_list_of_crags[0]]

    markers_recommended = []
    for ind in crags[crags.cragSlug.isin(sorted_list_of_crags)].index:
        marker = {
            'lat': crags.loc[ind, 'lat'],
            'lon': crags.loc[ind, 'long'],
            'name': crags.loc[ind, 'name'],
            'cragSlug': crags.loc[ind, 'cragSlug'],
            'cragName': crags.loc[ind, 'name'],
            'ascents': crags.loc[ind, 'ascents'],
            'routes': crags.loc[ind, 'routes'],
            'recommended_routes': recommended_crags[crags.loc[ind, 'cragSlug']],
            'size': 50 * (recommended_crags[crags.loc[ind, 'cragSlug']] + 10) / (max_routes_num + 10)
        }
        markers_recommended.append(marker)
    return render_template('index.html',
                           markers=markers_recommended,
                           crags_recommendation='on',
                           recommended_crags=sorted_list_of_crags,
                           crags_with_routes=recommended_crags,
                           data=dic_preferences,
                           cold_start=flag_cold_start
                           )


if __name__ == '__main__':
    application.run(host='0.0.0.0')
