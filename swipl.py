from pyswip import Prolog
from pyswip import Functor
from pyswip import Variable
from pyswip.prolog import PrologError

DEFAULT_LIMIT = 10

def format_value(value):
    output = ""
    if isinstance(value, list):
        output = "[ " + ", ".join([format_value(val) for val in value]) + " ]"
    elif isinstance(value, Functor) and value.arity == 2:
        output = "{0}{1}{2}".format(value.args[0], value.name, value.args[1])
    else:
        output = "{}".format(value)
    return output

def format_functor(functor):
    if not isinstance(functor, Functor):
        return str(functor)
    return "{}{}{}".format(format_functor(functor.args[0]), str(functor.name), format_functor(functor.args[1]))

def format_result(result, request, maxresults, prolog):
    result = list(result)

    if len(result) == 0:
        return "false."
    output = ""
    for i, res in enumerate(result):
        if len(res) == 0:
            output += "true;\n"
            continue
        tmpVarOutput = []
        vars = {}
        add_run = []
        for var in res:
            if isinstance(res[var], Variable):
                if not res[var].chars:
                    add_run.append(var)
                    continue
                id = res[var].chars
                if id in vars:
                    vars[id].append(var)
                else:
                    vars[id] = [var]
                    tmpVarOutput.append(res[var])
            else:
                tmpVarOutput.append(var + " = " + format_value(res[var]))
        tmpOutput = []
        for line in tmpVarOutput:
            if isinstance(line, Variable):
                id = line.chars
                if len(vars[id]) == 1:
                    tmpOutput.append(vars[id][0] + " = " + str(line))
                else:
                    tmpOutput.append(" = ".join(vars[id]))
            else:
                tmpOutput.append(line)
        if add_run:
            request = "{}, copy_term([{}], [{}], __ADD_INFO).".format(request, ", ".join(add_run), ", ".join(add_run))
            add_data = list(prolog.query(request, maxresult=maxresults))[i]['__ADD_INFO']
            for vi, v in enumerate(add_run):
                functor = add_data[vi].args[1]
                sub_functor = functor.args[1]
                v_res = "{} {} {}".format(v, str(functor.name), format_functor(functor.args[1]))
                tmpOutput.append(v_res)
        output += ", ".join(tmpOutput) + ";\n"
    output = output[:-2] + "."

    return output

def run(code):
    prolog = Prolog()

    output = []
    ok = True

    tmp = ""
    isQuery = False
    for line in code.split("\n"):
        line = line.split("%", 1)[0]
        line = line.strip()
        if line == "" or line[0] == "%":
            continue

        if line[:2] == "?-" or line[:2] == ":-":
            isQuery = True
            isSilent = line[:2] == ":-"
            line = line[2:]
        tmp += " " + line

        if tmp[-1] == ".":
            # End of statement
            tmp = tmp[:-1] # Removes "."
            maxresults = DEFAULT_LIMIT
            # Checks for maxresults
            if tmp[-1] == "}":
                tmp = tmp[:-1] # Removes "."
                limitStart = tmp.rfind('{')
                if limitStart == -1:
                    ok = False
                    output.append("ERROR: Found '}' before '.' but opening '{' is missing!")
                else:
                    limit = tmp[limitStart+1:]
                    try:
                        maxresults = int(limit)
                    except:
                        ok = False
                        output.append("ERROR: Invalid limit {" + limit + "}!")
                    tmp = tmp[:limitStart]

            try:
                if isQuery:
                    result = prolog.query(tmp, maxresult=maxresults)
                    formatted = format_result(result, tmp, maxresults, prolog)
                    if not isSilent:
                        output.append(formatted)
                    result.close()
                else:
                    prolog.assertz('(' + tmp + ')')
            except PrologError as error:
                ok = False
                output.append("ERROR: {}".format(error))

            tmp = ""
            isQuery = False

    return output, ok
