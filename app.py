import json
import secrets

import pandas as pd
from flask import Flask, render_template
from flask import request

from climbing_routes_info import list_styles, list_steepness
from grades_info import dict_for_clustered_grades, dict_for_names_grades, vl_dict_for_grades

application = Flask(__name__)
# set secret key:
# 'Drmhze6EPcv0fN_81Bj-nA'
application.secret_key = secrets.token_urlsafe(16)
crags = pd.read_csv('db/crags_Arco.csv', header=0,
                    names=['crag', 'latitude', 'longitude', 'vl_location_id', 'cragSlug'])
df_sportclimbing_routes = pd.read_csv('./db/sportclimbing_routes_tags.csv')
users_profiles = pd.read_csv('./db/users_Arco_routes2.csv')

username = 'admin'
password = 'admin'


def find_favourite_recommendation_for_crag(crag, discipline, style, grade, steepness, type_recommendation):
    """
    find amount of the suitable routes within the crag
    """
    list_styles_checked = []
    dic_styles = {}
    style = int(style, 2)
    for style_current, num in zip(list_styles, [100000, 10000, 1000, 100, 10, 1]):
        num = int(str(num), 2)
        if style & num > 0:
            dic_styles[style_current] = 1
            list_styles_checked.append(style_current)
        else:
            dic_styles[style_current] = 0
    list_steepness_checked = []
    dic_steepness = {}
    steepness = int(steepness, 2)
    if type_recommendation == 'favourite':
        for steepness_current, num in zip(list_steepness, [1000, 100, 10, 1]):
            num = int(str(num), 2)
            if steepness & num > 0:
                dic_steepness[steepness_current] = 1
                list_steepness_checked.append(steepness_current)
            else:
                dic_steepness[steepness_current] = 0
    elif type_recommendation == 'training':
        for steepness_current in list_steepness:
            dic_steepness[steepness_current] = 0
    grade_numbers = dict_for_clustered_grades[grade]
    cragSlug = crag["cragSlug"]
    num_routes_in_crag = 0
    ds_current_routes = df_sportclimbing_routes[df_sportclimbing_routes.cragSlug == cragSlug]
    result = ds_current_routes.to_json(orient="records")
    parsed = json.loads(result)
    for points in parsed:
        if (points['gradeIndex'] in grade_numbers) and \
                ((dic_styles['athletic'] != 1) or (points['athletic'] > 0)) and \
                ((dic_styles['cruxy'] != 1) or (points['cruxy'] > 0)) and \
                ((dic_styles['endurance'] != 1) or (points['endurance'] > 0)) and \
                ((dic_styles['crimpy'] != 1) or (points['crimpy'] > 0)) and \
                ((dic_styles['sloper'] != 1) or (points['sloper'] > 0)) and \
                ((dic_styles['technical'] != 1) or (points['technical'] > 0)):
            # TODO: steepness is not working for now
            # and \
            # ((dic_steepness['vertical'] != 1) or (points['vertical'] > 0)) and \
            # ((dic_steepness['overhang'] != 1) or (points['overhang'] > 0)) and \
            # ((dic_steepness['roof'] != 1) or (points['roof'] > 0)) and \
            # ((dic_steepness['slab'] != 1) or (points['slab'] > 0)):
            num_routes_in_crag += 1
    if num_routes_in_crag > 0:
        return num_routes_in_crag
    else:
        return 0


@application.route("/", methods=('GET', 'POST'))
def index():
    error = None
    if request.method == 'POST':
        if request.form['username'] != username or request.form['password'] != password:
            error = 'Invalid Credentials. Please try again.'
        else:
            return render_template('index.html', error=error)
    return render_template('login.html', error=error)


@application.route("/login", methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        user_id_entered = int(request.form['username'])
        password_entered = request.form['password']
        user_data = users_profiles[users_profiles['user_id'] == user_id_entered]
        if len(user_data) > 0 and password_entered == password:
            return render_template('index.html',
                                   user_id=user_id_entered,
                                   least_fav_style=user_data.least_fav_style.values[0],
                                   fav_style=user_data.fav_style.values[0],
                                   fav_steepness=user_data.fav_steepness.values[0],
                                   fav_grade=dict_for_names_grades[vl_dict_for_grades[user_data.fav_grade.values[0]]]
                                   )
        else:
            error = 'Invalid Credentials. Please try again.'
            return render_template('login.html', error=error)
    else:
        return render_template('login.html', error='')


@application.route("/recommended_crags", methods=('GET', 'POST'))
def recommended_crags():
    args = request.args
    discipline = args.get('discipline')
    style = args.get('style')
    least_style = args.get('least_style')
    grade = args.get('grade')
    steepness = args.get('steepness')

    type_recommendation = args.get('type_recommendation')
    if type_recommendation == 'training':
        recommended_style = least_style
    elif type_recommendation == 'favourite':
        recommended_style = style
    items = list()
    num_recommended_crags = 0
    for _, crag in crags.iterrows():
        n = crag['crag']
        s = crag['cragSlug']
        lat = crag['latitude']
        lon = crag['longitude']
        crag_is_recommended = False
        if (discipline is not None) and (style is not None) and (grade is not None):  # and (steepness is not None):
            if steepness is None:
                steepness = '0'
            number_suited_routes = find_favourite_recommendation_for_crag(crag, discipline, recommended_style, grade,
                                                                          steepness, type_recommendation)
            if number_suited_routes > 0:
                crag_is_recommended = True
                num_recommended_crags += 1
        r = crag_is_recommended
        item = {
            'cragName': n,
            'cragSlug': s,
            'latitude': lat,
            'longitude': lon,
            'isRecommended': r
        }
        items.append(item)
    # TODO: here if there is no recommendations are given, we should give 10-top visited crags
    response = {'items': items}

    return response


@application.route("/routes", methods=('GET', 'POST'))
def routes():
    favourite_flag, training_flag, motivation_flag, error_flag, give_rec_flag, from_crags_page = [False for _ in
                                                                                                  range(6)]
    error_message = ''
    action = ''
    if request.method == 'POST':
        # from routes request
        action = request.form['action']
        steepnesses = request.form.getlist('steepness')
        cstyles = request.form.getlist('cstyle')
        least_styles = request.form.getlist('least_style')
        grade = request.form['grade']
        discipline = request.form['discipline']
        type_recommendation = request.form['type_recommendation']
        cragSlug = request.form['cragSlug']
        cragName = request.form['cragName']
    else:
        # from crags request
        args = request.args
        discipline = args.get('discipline')
        cragSlug = args.get('cragSlug')
        cragName = args.get('cragName')
        cstyles = []
        for each_style in list_styles:
            if args.get(each_style) == 'true':
                cstyles.append(each_style)
        least_styles = []
        for each_style in list_styles:
            if args.get('least_' + each_style) == 'true':
                least_styles.append(each_style)
        steepnesses = []
        for each_steepness in list_steepness:
            if args.get(each_steepness) == 'true':
                steepnesses.append(each_steepness)
        grade = args.get('grade')
        type_recommendation = args.get('type_recommendation')
        from_crags_page = True
    if grade != '':
        list_grades = dict_for_clustered_grades[grade]

    if type_recommendation == 'training':
        training_flag = True
    elif type_recommendation == 'favourite':
        favourite_flag = True
    elif type_recommendation == 'motivation':
        motivation_flag = True
    if not from_crags_page and (
            (len(cstyles) > 0 and favourite_flag) or (len(least_styles) > 0 and training_flag)) and (
            len(grade) > 0) and (len(discipline) > 0):
        give_rec_flag = True

    if action == 'home':
        give_rec_flag = False
    elif action == 'recommend':
        if len(discipline) == 0:
            error_message += 'favourite discipline should be inserted; <br>'
        if len(cstyles) == 0:
            error_message += 'favourite style should be inserted; <br>'
        if len(least_styles) == 0:
            error_message += 'least favourite style should be inserted; <br>'
        if len(grade) == 0:
            error_message += 'favourite grades should be inserted; <br>'
        # if len(steepnesses) == 0:
        #    error_message += 'wall steepness should be inserted; <br>'
    if len(error_message) > 0:
        error_flag = True
        give_rec_flag = True
    ds_current_routes = df_sportclimbing_routes[df_sportclimbing_routes.cragSlug == cragSlug]
    result = ds_current_routes.to_json(orient="records")
    parsed = json.loads(result)
    sportclimbing = {}

    for points in parsed:
        grade_fl, style_fl, steepness_fl = [False, False, False]
        if give_rec_flag and (points['gradeIndex'] in list_grades):
            grade_fl = True
        # recommendations for favourite moves
        if give_rec_flag and favourite_flag:
            for each_style in cstyles:
                if points[each_style] > 0:
                    style_fl = True
            # TODO: sort according to steepness value
            for each_steepness in steepnesses:
                if points[each_steepness] > 0:
                    steepness_fl = True
        # recommendations for training
        elif give_rec_flag and training_flag:
            for each_style in least_styles:
                if points[each_style] > 0:
                    style_fl = True
        # recommendation for motivation
        # doesn't matter which style
        elif give_rec_flag and motivation_flag:
            style_fl = True
        # TODO: grade prediction model

        if give_rec_flag and ((grade_fl and style_fl and favourite_flag) or (
                grade_fl and style_fl and training_flag) or (grade_fl and motivation_flag)):
            if points['sectorSlug'] not in sportclimbing.keys():
                sportclimbing[points['sectorSlug']] = [points]
            else:
                sportclimbing[points['sectorSlug']].append(points)
        elif not give_rec_flag:
            if points['sectorSlug'] not in sportclimbing.keys():
                sportclimbing[points['sectorSlug']] = [points]
            else:
                sportclimbing[points['sectorSlug']].append(points)

    result_json = {'cragName': cragName,
                   'cragSlug': cragSlug,
                   'sportclimbing': sportclimbing,
                   'give_rec_fl': give_rec_flag,
                   'steepnesses': steepnesses,
                   'cstyles': cstyles,
                   'grade': grade,
                   'discipline': discipline,
                   'least_styles': least_styles,
                   'type_recommendation': type_recommendation,
                   'error_flag': error_flag,
                   'error_message': error_message
                   }

    return render_template('routes.html', data=result_json)


@application.route("/massone", methods=('GET', 'POST'))
def massone():
    favourite_flag, training_flag, motivation_flag, error_flag, give_rec_flag, from_crags_page = [False for _ in
                                                                                                  range(6)]
    error_message = ''
    action = ''
    if request.method == 'POST':
        # from routes request
        action = request.form['action']
        steepnesses = request.form.getlist('steepness')
        cstyles = request.form.getlist('cstyle')
        least_styles = request.form.getlist('least_style')
        grade = request.form['grade']
        discipline = request.form['discipline']
        type_recommendation = request.form['type_recommendation']
        user_id = request.form['user_id']
        cragSlug = 'massone'
        cragName = 'Massone'
    else:
        # from crags request
        args = request.args
        discipline = args.get('discipline')
        user_id = args.get('user_id')
        cragSlug = args.get('cragSlug')
        cragName = args.get('cragName')
        cstyles = []
        for each_style in list_styles:
            if args.get(each_style) == 'true':
                cstyles.append(each_style)
        least_styles = []
        for each_style in list_styles:
            if args.get('least_' + each_style) == 'true':
                least_styles.append(each_style)
        steepnesses = []
        for each_steepness in list_steepness:
            if args.get(each_steepness) == 'true':
                steepnesses.append(each_steepness)
        grade = args.get('grade')
        type_recommendation = args.get('type_recommendation')
        from_crags_page = True
    if grade != '':
        list_grades = dict_for_clustered_grades[grade]

    if type_recommendation == 'training':
        training_flag = True
    elif type_recommendation == 'favourite':
        favourite_flag = True
    elif type_recommendation == 'motivation':
        motivation_flag = True
    if not from_crags_page and (
            (len(cstyles) > 0 and favourite_flag) or (len(least_styles) > 0 and training_flag) or (
                motivation_flag)) and (len(grade) > 0):
        give_rec_flag = True

    if action == 'home':
        give_rec_flag = False
    elif action == 'recommend':
        if len(discipline) == 0:
            error_message += 'favourite discipline should be inserted; <br>'
        if len(cstyles) == 0:
            error_message += 'favourite style should be inserted; <br>'
        if len(least_styles) == 0:
            error_message += 'least favourite style should be inserted; <br>'
        if len(grade) == 0:
            error_message += 'favourite grades should be inserted; <br>'
        # if len(steepnesses) == 0:
        #    error_message += 'wall steepness should be inserted; <br>'
    if len(error_message) > 0:
        error_flag = True
        give_rec_flag = True

    routes_Massone = pd.read_csv('db/massone_tags.csv')
    routes_sector_B = routes_Massone[routes_Massone.sector_id == 5289]
    routes_sector_B = routes_sector_B.sort_values(by=['topo_num'], ascending=True)
    sportclimbing = {}

    for i, data in routes_sector_B.iterrows():
        grade_fl, style_fl, steepness_fl, perceived_grade = [False, False, False, False]
        jsonStr = data.to_json()
        parsed = json.loads(jsonStr)

        if give_rec_flag and (int(parsed['grade'][3:]) in list_grades):
            grade_fl = True
        # recommendations for favourite moves
        if give_rec_flag and favourite_flag:
            for each_style in cstyles:
                if parsed[each_style] > 0:
                    style_fl = True
            # TODO: sort according to steepness value
            for each_steepness in steepnesses:
                if parsed[each_steepness] > 0:
                    steepness_fl = True
        # recommendations for training
        elif give_rec_flag and training_flag:
            for each_style in least_styles:
                if parsed[each_style] > 0:
                    style_fl = True
        elif give_rec_flag and motivation_flag:
            if parsed['mean_deviation'] < 0:
                perceived_grade = True
        if give_rec_flag and ((grade_fl and style_fl and favourite_flag) or (
                grade_fl and style_fl and training_flag) or (grade_fl and perceived_grade)):
            sportclimbing[data.topo_num] = parsed
        elif not give_rec_flag:
            sportclimbing[data.topo_num] = parsed

        if data.topo_num > 24:
            break
    if len(sportclimbing.keys()) == 0 and not error_flag:
        error_flag = True
        error_message = 'No recommendations have been found for the preferences defined'
    result_json = {'cragName': 'Massone',
                   'cragSlug': 'massone',
                   'sportclimbing': sportclimbing,
                   'give_rec_fl': give_rec_flag,
                   'user_id': user_id,
                   'steepnesses': steepnesses,
                   'cstyles': cstyles,
                   'grade': grade,
                   'discipline': discipline,
                   'least_styles': least_styles,
                   'type_recommendation': type_recommendation,
                   'error_flag': error_flag,
                   'error_message': error_message
                   }

    return render_template('massone.html', data=result_json)


if __name__ == '__main__':
    application.run(host='0.0.0.0')
