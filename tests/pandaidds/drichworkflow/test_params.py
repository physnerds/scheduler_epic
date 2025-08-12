if __name__ == "__main__":
    # move imports here
    # so the remote execution will not import these libraries

    import argparse
    from ProjectUtils.config_editor import *

    #from ax import SumConstraint
    #from ax import OrderConstraint
    from ax.core.parameter_constraint import ParameterConstraint
    from ax.core.search_space import SearchSpace
    from ax.core.parameter import RangeParameter,ParameterType


    def constraint_ax(constraints,parameters):
        # constraint_dict: Dict[str,float], bound: float
        constraint_list = []
        for c in constraints:
            param_dict = {}
            param_list = constraints[c]["parameters"]
            for param in parameters:
                if param in param_list:
                    param_dict[param] = constraints[c]["weights"][param_list.index(param)]
                else:
                    param_dict[param] = 0
            print("param dict: ", param_dict, " param_list: ", param_list)
            constraint_list.append( ParameterConstraint(param_dict,constraints[c]["bound"]) )
        return constraint_list

        
    parser = argparse.ArgumentParser(description="Optimization, dRICH")
    parser.add_argument('-n', '--name', help='workflow name', type=str, default='drich-mobo')
    parser.add_argument('-d', '--detparameters', 
                        help='Detector parameter configuration file', 
                        type = str, required = True)

    args = parser.parse_args()
    detconfig = ReadJsonFile(args.detparameters)
    # get the json of parameters
    print(detconfig['constraints'])

    parameters = list(detconfig['parameters'].keys())
    print(parameters)

    constraints_ax = constraint_ax(detconfig['constraints'],parameters)
    print("constraints_ax ..................")
    print(constraints_ax)

    """
    search_space = SearchSpace(
        parameters=[
            RangeParameter(
                name=i,
                lower=float(detconfig["parameters"][i]["lower"]),
                upper=float(detconfig["parameters"][i]["upper"]),
                parameter_type=ParameterType.FLOAT,
            )
            for i in detconfig["parameters"]
        ]
    )
    """
    search_space = [
    {
        "name": name,
        "type": "range",
        "bounds": [
            float(detconfig["parameters"][name]["lower"]),
            float(detconfig["parameters"][name]["upper"])
        ],
        "value_type": "float"
    }
    for name in detconfig["parameters"]
    ]
    
    print("search_space .................")
    print(search_space)

    


    