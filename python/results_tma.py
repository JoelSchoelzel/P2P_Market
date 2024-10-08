import pickle
import os

def load_results():
    directory = r"C:\Users\jsc-tma\Masterarbeit_tma\Optimierung\results\old\Medium District 12houses BOI+HP+CHP\3_Mar\nB=3"
    
    init_val_path = os.path.join(directory, 'init_val_P2P.p')
    rows_path = os.path.join(directory, 'rows_P2P.p')
    opti_res_path = os.path.join(directory, 'opti_res_P2P.p')
    par_rh_path = os.path.join(directory, 'par_rh_P2P.p')
    mar_dict_path = os.path.join(directory, 'mar_dict_P2P.p')

    with open(init_val_path, "rb") as f:
        init_val = pickle.load(f)
    with open(rows_path, "rb") as f:
        rows = pickle.load(f)
    with open(opti_res_path, "rb") as f:
        opti_res = pickle.load(f)
    with open(par_rh_path, "rb") as f:
        par_rh = pickle.load(f)
    with open(mar_dict_path, "rb") as f:
        mar_dict = pickle.load(f)

    return init_val, rows, opti_res, par_rh, mar_dict

init_val, rows, opti_res, par_rh, mar_dict = load_results()
print("HI")
