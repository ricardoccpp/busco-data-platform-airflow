#!/usr/bin/env bash
# Script para aguardar até que um host e porta estejam disponíveis
# Adaptado de https://github.com/vishnubob/wait-for-it

WAITFORIT_cmdname=${0##*/}

echoerr() { if [[ $WAITFORIT_QUIET -ne 1 ]]; then echo "$@" 1>&2; fi }

usage()
{
    cat << USAGE >&2
Usage:
    $WAITFORIT_cmdname host:port [-s] [-t timeout] [-- command args]
    -h HOST | --host=HOST       Host or IP to verify
    -p PORT | --port=PORT       TCP port to verify
    -s | --strict               Falha caso timeout seja atingido
    -q | --quiet                Não exibe mensagens de erro
    -t TIMEOUT | --timeout=TIMEOUT
                                Timeout em segundos, 0 para sem timeout
    -- COMMAND ARGS             Executa comando com args após a verificação
USAGE
    exit 1
}

wait_for()
{
    if [[ $WAITFORIT_TIMEOUT -gt 0 ]]; then
        echoerr "$WAITFORIT_cmdname: Aguardando $WAITFORIT_HOST:$WAITFORIT_PORT por $WAITFORIT_TIMEOUT segundos"
    else
        echoerr "$WAITFORIT_cmdname: Aguardando $WAITFORIT_HOST:$WAITFORIT_PORT sem timeout"
    fi
    
    WAITFORIT_start_ts=$(date +%s)
    while :
    do
        if [[ $WAITFORIT_TIMEOUT -gt 0 && ($(date +%s) - $WAITFORIT_start_ts) -gt $WAITFORIT_TIMEOUT ]]; then
            echoerr "$WAITFORIT_cmdname: Timeout atingido"
            break
        fi
        nc -z $WAITFORIT_HOST $WAITFORIT_PORT > /dev/null 2>&1
        
        WAITFORIT_result=$?
        
        if [[ $WAITFORIT_result -eq 0 ]]; then
            WAITFORIT_end_ts=$(date +%s)
            echoerr "$WAITFORIT_cmdname: $WAITFORIT_HOST:$WAITFORIT_PORT está disponível após $((WAITFORIT_end_ts - WAITFORIT_start_ts)) segundos"
            break
        fi
        sleep 1
    done
    return $WAITFORIT_result
}

wait_for_wrapper()
{
    # Executa em um subshell para evitar contaminar o ambiente atual
    wait_for
    WAITFORIT_result=$?
    if [[ $WAITFORIT_result -ne 0 ]]; then
        if [[ $WAITFORIT_STRICT -eq 1 ]]; then
            exit $WAITFORIT_result
        fi
    fi
    if [[ $WAITFORIT_result -eq 0 ]]; then
        # Os args podem ser passados como '$@' para manter aspas duplas
        exec "${WAITFORIT_CLI[@]}"
    else
        echoerr "$WAITFORIT_cmdname: $WAITFORIT_HOST:$WAITFORIT_PORT não está disponível"
        exit 1
    fi
}

# Processar argumentos
while [[ $# -gt 0 ]]
do
    case "$1" in
        *:* )
        WAITFORIT_hostport=(${1//:/ })
        WAITFORIT_HOST=${WAITFORIT_hostport[0]}
        WAITFORIT_PORT=${WAITFORIT_hostport[1]}
        shift 1
        ;;
        --host=*)
        WAITFORIT_HOST="${1#*=}"
        shift 1
        ;;
        --port=*)
        WAITFORIT_PORT="${1#*=}"
        shift 1
        ;;
        -q | --quiet)
        WAITFORIT_QUIET=1
        shift 1
        ;;
        -s | --strict)
        WAITFORIT_STRICT=1
        shift 1
        ;;
        -t)
        WAITFORIT_TIMEOUT="$2"
        if [[ $WAITFORIT_TIMEOUT == "" ]]; then break; fi
        shift 2
        ;;
        --timeout=*)
        WAITFORIT_TIMEOUT="${1#*=}"
        shift 1
        ;;
        --)
        shift
        WAITFORIT_CLI=("$@")
        break
        ;;
        --help)
        usage
        ;;
        *)
        echoerr "Argumento desconhecido: $1"
        usage
        ;;
    esac
done

if [[ "$WAITFORIT_HOST" == "" || "$WAITFORIT_PORT" == "" ]]; then
    echoerr "Erro: você precisa fornecer um host e porta para testar."
    usage
fi

WAITFORIT_TIMEOUT=${WAITFORIT_TIMEOUT:-15}
WAITFORIT_STRICT=${WAITFORIT_STRICT:-0}
WAITFORIT_QUIET=${WAITFORIT_QUIET:-0}

# Verificar se o comando está presente
if [[ -n $WAITFORIT_CLI ]]; then
    wait_for_wrapper
else
    wait_for
    WAITFORIT_result=$?
    exit $WAITFORIT_result
fi