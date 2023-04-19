from app import app
from flask import jsonify
from flask import request, url_for
import os
from werkzeug.utils import secure_filename
from entities.Response import Success, Error, SuccessList
from entities.Comparators import Comparators
from entities.ComparatorsResult import ComparatorsResults
from entities.SystematicReview import SystematicReview
from entities.Amstar import Amstar
import json
import requests
import time
import ast
import numpy as np
from infra import PdfMiner
from entities.URL import URL

UPLOAD_FOLDER = os.getcwd()+'/uploads'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def calc(str, key, files):
    def start_bias() :
        return {
            "domain": '',
            "judgement": '',
            "label": '',
            "score": 0,
        }
    response = []
    BIAS_MAP = {
        "high/unclear": { "score": 0, "label": "+" },
        "low": { "score": 1, "label": "?" },
    }
    partial_n = dict()
    partial_n["items"] = dict()
    partial_n["total"] = 0
    partial_n["result"] = 0


    bias = dict()
    bias["random_sequence_generation"] = dict()
    bias["allocation_concealment"] = dict()
    bias["blinding_of_participants_and_personnel"] = dict()
    bias["blinding_of_outcome_assessment"] = dict()

    authors = dict()

    count=1
    for article in str['article_data']:
        file = article['gold']['filename'].replace(" ", "_") if "gold" in article and "filename" in article['gold'] else '-'

        if file not in files[key]: continue
        
        sample_size = article["ml"]["sample_size"]

        if "?" in  sample_size:
            partial_n["result"] = -1
        else:
            partial_n["result"] = int(partial_n["result"]) + int(sample_size)

        try:
            author = article["grobid"]["authors"][0]
        except:
            author = "?"
        year = 0
        if "year" in article["grobid"]:
            year =  article["grobid"]["year"]
        else:
            if "pubmed" in article["grobid"] and "year" in article["grobid"]["pubmed"]:
                year = article["grobid"]["pubmed"]["year"]
        try:
            trial = f'{author["lastname"]} {author["initials"]}, {year}'
        except:
            trial = "?"
        

        partial_n["items"][trial] = sample_size
        random_sequence_generation = start_bias()
        allocation_concealment  = start_bias()
        blinding_of_participants_and_personnel  = start_bias()
        blinding_of_outcome_assessment  = start_bias()
        if "rct" not in article['ml']:
            response.append({
                "sample_size": sample_size,
                "trial": '',
                "design": '',
                "random_sequence_generation": random_sequence_generation,
                "allocation_concealment": allocation_concealment,
                "blinding_of_participants_and_personnel": blinding_of_participants_and_personnel,
                "blinding_of_outcome_assessment": blinding_of_outcome_assessment,
                'is_rct': False,
                'file': file
            })
            continue

        design = "RCT" if article["ml"]["rct"]["is_rct"] else "-"
        
        

        random_sequence_generation = {
            "domain": article["ml"]["bias"][0]["domain"],
            "judgement": article["ml"]["bias"][0]["judgement"],
            "label": BIAS_MAP[article["ml"]["bias"][0]["judgement"]]["label"],
            "score": BIAS_MAP[article["ml"]["bias"][0]["judgement"]]["score"],
        }

        bias["random_sequence_generation"][trial] = BIAS_MAP[article["ml"]["bias"][0]["judgement"]]["score"]

        allocation_concealment = {
            "domain": article["ml"]["bias"][1]["domain"],
            "judgement": article["ml"]["bias"][1]["judgement"],
            "label": BIAS_MAP[article["ml"]["bias"][1]["judgement"]]["label"],
            "score": BIAS_MAP[article["ml"]["bias"][1]["judgement"]]["score"],
        }
        
        bias["allocation_concealment"][trial] = BIAS_MAP[article["ml"]["bias"][1]["judgement"]]["score"]

        blinding_of_participants_and_personnel = {
            "domain": article["ml"]["bias"][2]["domain"],
            "judgement": article["ml"]["bias"][2]["judgement"],
            "label": BIAS_MAP[article["ml"]["bias"][2]["judgement"]]["label"],
            "score": BIAS_MAP[article["ml"]["bias"][2]["judgement"]]["score"],
        }
        
        bias["blinding_of_participants_and_personnel"][trial] = BIAS_MAP[article["ml"]["bias"][2]["judgement"]]["score"]


        blinding_of_outcome_assessment = {
            "domain": article["ml"]["bias"][3]["domain"],
            "judgement": article["ml"]["bias"][3]["judgement"],
            "label": BIAS_MAP[article["ml"]["bias"][3]["judgement"]]["label"],
            "score": BIAS_MAP[article["ml"]["bias"][3]["judgement"]]["score"],
        }
        
        bias["blinding_of_outcome_assessment"][trial] = BIAS_MAP[article["ml"]["bias"][3]["judgement"]]["score"]
        count= count+1
        is_rct = article['ml']['rct']['is_rct']
        response.append({
            "file": file, 
            'is_rct':is_rct,
            "sample_size": sample_size,
            "trial": trial,
            "design": design,
            "random_sequence_generation": random_sequence_generation,
            "allocation_concealment": allocation_concealment,
            "blinding_of_participants_and_personnel": blinding_of_participants_and_personnel,
            "blinding_of_outcome_assessment": blinding_of_outcome_assessment,
        })
    return response, bias, partial_n, authors


def downgrade_num_participantes( row ):
    sample_size = row["sample_size"]
    downgrade = 0
    if "?" in  sample_size:
        return -2
    if ( int(sample_size) >= 200 ):
        return 0
    if ( int(sample_size) >= 100 and int(sample_size) <= 199 ):
        return -1
    if ( int(sample_size) >= 1 and int(sample_size) <= 99 ):
        return -2
    
def downgrade_risco_vies( row ):

    target = [
        "allocation_concealment",
        "blinding_of_outcome_assessment",
        "blinding_of_participants_and_personnel",
        "random_sequence_generation"
    ]
    count = 0
    for t in target:
        count = count + (row[t]["score"] * 0.25)

    return 0 if count >= 0.5 else -1

def downgrade_risco_vies_json( row ):

    target = [
        "allocation_concealment",
        "blinding_of_outcome_assessment",
        "blinding_of_participants_and_personnel",
        "random_sequence_generation"
    ]
    result = dict()
    result["items"] = dict()
    result["labels"] = dict()
    
    for i, t in enumerate(target):
        result["items"][f'item{i+1}'] = True if row[t]["score"] else False
        result["labels"][i+1] = t


    return result


def calc_score(part):
    sample_size = part["sample_size"]
    trial = part["trial"]
    downgrade_n_participantes = downgrade_num_participantes(part)
    risco_vies = downgrade_risco_vies(part)
    risco_vies_json = downgrade_risco_vies_json(part)
    return trial, downgrade_n_participantes, risco_vies, risco_vies_json


@app.route("/comparators", methods=['POST'])
def save_comparators():
    """
    [
        {
            comparators: {
                outcome: string,
                intervention: string,
                comparator: string
            },
            files: []
        }
    ]
    """
    if 'uid' not in request.form:
        return Error.body('No UID passed')
    
    if 'files' not in request.files:
        return  Error.body('No files')

    uid = request.form.get('uid')
    outcome = request.form.get('outcome')
    intervention = request.form.get('intervention')
    comparator  = request.form.get('comparator')

    files = request.files.getlist('files')
    for file in files:
        if file.filename == '':
            return  Error.body('No selected file')
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            file.save(filepath)
            
            comparatorResponse = Comparators(
                uid, outcome, intervention, comparator,
                filepath, done=0, result='', created_at=None
            )
            comparatorResponse.save()
    
    return Success.body('Comparator cretead')

@app.route("/comparators/<uid>", methods=['GET'])
def find_comparators_uid(uid):
    comparatorList = Comparators.find_id(uid)
    comparatorList = [ i.__dict__ for i in comparatorList]
    return SuccessList.body(comparatorList)


@app.route("/comparators-robot/<uid>", methods=['GET'])
def send_to_robotreviwer(uid):
    comparatorList = Comparators.find_id(uid)
    url = f'http://{URL}:5050/upload_and_annotate_pdfs'
    file = []
    
    headers = {"Content-Type": "multipart/form-data; charset=utf-8"}

    _file = set()
    for comparator in comparatorList:
        _file.add(comparator.path_files)


    for comparator in _file:

        with open(comparator, "rb") as f:
            file.append(('file', (comparator, f.read(), "multipart/form-data")))
   
    test_response = requests.post(url, files = file)
    response = test_response.json()
    report_uuid = response['report_uuid']
    Comparators.update_uid_report_id( uid, response['report_uuid'])

    return handle_robot_reviewer_job(uid)


@app.route("/comparators-robot-job/<uid>", methods=['GET'])
def handle_robot_reviewer_job(uid):

    comparators = Comparators.find_id(uid)
    report_uuid = comparators[0].report_id

    url_check = f'http://{URL}:5050/annotate_status/{report_uuid}'
    response_check = requests.get( url_check).json()
    print(f'response_check: {response_check}')

    complete = False
   
    print(report_uuid)

    if 'meta' in response_check and response_check['meta'] is not None:
        for i in range(1, 51):
            if response_check['meta']['process_percentage'] != 100:
                time.sleep(2)
                response_check = requests.get( url_check).json()
                print(f'response_check: {response_check}')
            if response_check['meta']['process_percentage'] == 100:
                complete = True
                break
    if 'meta' in response_check and response_check['meta'] is not None:
        if response_check['meta']['process_percentage'] == 100:
            url_result = f'http://{URL}:5050/report_view/{report_uuid}/json'
            response_result = requests.get(url_result).text
            with open( f'{UPLOAD_FOLDER}/{report_uuid}.json', 'w') as f:
                f.write(response_result)
            response_result = f'{UPLOAD_FOLDER}/{report_uuid}.json'

            print( f'response_result: {response_result}')
            Comparators.update_uid_result( uid, response_result)
    print(report_uuid)
    return Success.body('ok' )



@app.route("/comparators-calc/<uid>", methods=['GET'])
def comparators_calc(uid):
    comparators_results = ComparatorsResults.find_results(uid)
    comparatos_list = set()
    result = dict()
    files = {}
    
    for comp in comparators_results:
        file_key = f'{comp.outcome}|{comp.intervention}|{comp.comparator}'
        if file_key in files:
            files[file_key].append( comp.path )
        else:
            files[file_key] = []
            files[file_key].append( comp.path )
        key_list=[]
        if comp.outcome:
            key_list.append(f"{comp.outcome}")
        if comp.intervention:
            key_list.append(f"{comp.intervention}")
        if comp.comparator:
            key_list.append(f"{comp.comparator}")
        key = ",".join(key_list)
        if key not in comparatos_list:
            comparatos_list.add(key)
            result[key] = { 
                "result": comp.result,
                "outcome":comp.outcome,
                "intervention": comp.intervention,
                "comparator": comp.comparator,
                'key': file_key
            }

    final_result = dict()
    authors = dict()
    for r in result:
        if r not in final_result:
            final_result[r]=dict()
        result_json = ''
        with open( result[r]['result'], 'r') as f:
            result_json = json.load(f)

        data = result_json
        result1, bias, sample, authors = calc(data, result[r]['key'], files)
        for response in result1:
            trial, downgrade_n_participantes, risco_vies, risco_vies_json= calc_score(response)
            final_result[r]["downgrade_n_participantes"] = downgrade_n_participantes
            final_result[r]["risco_vies"] = risco_vies
            final_result[r]["risco_vies_json"] = risco_vies_json
            final_result[r]["i2_score"] = 0
            final_result[r]["is_rct"] = response['is_rct']

        final_result[r]["outcome"] = result[r]["outcome"]
        final_result[r]["intervention"] = result[r]["intervention"]
        final_result[r]["comparator"] = result[r]["comparator"]
        final_result[r]["bias"] = bias
        final_result[r]["sample"] = sample

    systematic_review = SystematicReview.find_id(uid)
    i2_str = systematic_review[0].result
    path = systematic_review[0].path
    i2 = ast.literal_eval(i2_str)
    
    i2_result = dict()
    for i in i2:
        for r in final_result:
            tags = r.split(',')
            i_np = np.array(i[:-2])
            tag_np = np.array(tags)
            if np.isin(i_np, tag_np).all():
                final_result[r]["i2"] = i[len(i)-2]
                final_result[r]["i2_score"] = i[len(i)-1]

   
    text = PdfMiner.convert_pdf_to_string(path)

    amstar = Amstar(text)
    amstar_result = amstar.result()
    amstar_score = amstar_result["result"]
    amstar_values = list(amstar_result.values())
    amstar_saida = {
        "items": dict(),
        "lables": {
            "1": "allocation_concealment",
            "2": "blinding_of_outcome_assessment",
            "3": "blinding_of_participants_and_personnel",
            "4": "random_sequence_generation",
        },
        "result": amstar_values[4]
    }
    for i in range(4):
        amstar_saida["items"][f'item{(1+i)}'] = amstar_values[i]



    final_json = []
    for r in final_result:
        final_result[r]["amstar_score"] = amstar_score
        final_result[r]["final_score"] = final_result[r]["risco_vies"] + final_result[r]["downgrade_n_participantes"] + final_result[r]["i2_score"] + amstar_score
        final_result[r]["risco_vies_json"]["result"] = final_result[r]["amstar_score"]
        final_result[r]["i2_json"] = dict()
        final_result[r]["i2_json"]["heterogeneity"] = dict()
        final_result[r]["i2_json"]["heterogeneity"]["i2"] = final_result[r]["i2"].replace('I2', '').replace('I²', '').replace('=','').replace(' ','') if "i2" in final_result[r] else 0
        final_result[r]["i2_json"]["heterogeneity"]["result"] = final_result[r]["i2_score"]
        
        _json=dict()
        _json["values"] = [
            {
                "label": final_result[r]["outcome"],
                "value": final_result[r]["outcome"]
            },
            {
                "label": final_result[r]["intervention"],
                "value": final_result[r]["intervention"]
            },
            {
                "label": final_result[r]["comparator"],
                "value": final_result[r]["comparator"]
            },
        ]
        
        _json["result"] = dict()
        _json["result"]["number_of_participants"] = final_result[r]["sample"]
        _json["result"]["risk_of_bias"] = final_result[r]["bias"]
        _json["result"]["heterogeneity"] = final_result[r]["i2_json"]["heterogeneity"]
        _json["result"]["amstar"] = amstar_saida
        _json["result"]["amstar_result"] = amstar_values[4]
        _json["result"]["is_rct"] = final_result[r]["is_rct"]

        final_json.append(_json)
    
    return Success.body(final_json)


