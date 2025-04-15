import contextlib
import datetime
import json
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity as sklearn_cos
from scipy.spatial.distance import cosine as scipy_cos
import pandas as pd

#FUNCTION get time
def get_c_time():
    """Function for getting current time

    Returns:
        current_t_s (str): String of current time
    """
    current_t_s = datetime.datetime.now().strftime("%m-%d-%Y-%H-%M-%S")
    return current_t_s

#FUNCTION Clean String vals
def clean_string_values(obj):
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, str):
                value = value.replace("\\r\\n", "")
                with contextlib.suppress(json.JSONDecodeError):
                    value = json.loads(value)

            cleaned_value = clean_string_values(value)
            obj[key] = cleaned_value
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            cleaned_value = clean_string_values(value)
            obj[i] = cleaned_value
    elif isinstance(obj, str):
        obj = obj.replace("\\r\\n", "").replace('\\"', '"')

    return obj

# def clean_vectorize(srch_text:str, srch_field, node):
#     data_fields = [x[srch_field] for x in node.children if srch_field in node.children.data.keys()]
#     base_params = {
#         "binary":False, 
#         "norm":None,
#         "use_idf":False, 
#         "smooth_idf":False,
#         "lowercase":True, 
#         "stop_words":"english",
#         "min_df":1, 
#         "max_df":1.0, 
#         "max_features":None,  
#         "ngram_range":(1, 1)
#     }
#     model = TfidfVectorizer(**base_params)
#     tsfrm = model.fit_transform(data_fields)
#     feats = model.get_feature_names_out()
#     tsfrm_df = pd.DataFrame(
#         tsfrm.toarray(),
#         columns=feats,
#         index=DOI
# 	)
#     return tsfrm_df


def cosine_similarity(tsfrm, ts_type:str):
	"""Function that allows you to use either sklearns, or scipy's cosine similarity
	Inputs need to be a sparse array.  Scipy uses np.arrays, but the code 
	below will handle that. 

	Args:
		tsfrm (sparse array): Sparse Matrix of Documents
		ts_type (str): Version of Cosine Similarity you want

	Raises:
		ValueError: If you don't specify "scipy" or "sklearn", it throws an error.

	Returns:
		float: Cosine similarity
	"""	
    
	if ts_type == "sklearn":
		sims = sklearn_cos(tsfrm[0], tsfrm)
		return sims.flatten()
	
	elif ts_type == "scipy":
		sims = []
		X = tsfrm[0:1].toarray().flatten()
		for row in range(tsfrm.shape[0]):
			y = tsfrm[row].toarray().flatten()
			sims.append(1 - scipy_cos(X, y))
		return sims
	else:
		raise ValueError (f"{ts_type} not an available cosine transform. Check spelling for scipy or sklearn")
