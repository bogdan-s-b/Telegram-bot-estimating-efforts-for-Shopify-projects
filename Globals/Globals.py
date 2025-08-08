
from prime_util import *

# TODO: ### FIGMA API INITIALIZATION ###



headers = {
    'X-Figma-Token': FIGMA_API_TOKEN
}

# TODO: ### OPENAI ASSISTANT INITIALIZATION ###

INSTRUCTIONS = ""


openai.api_key = OPENAI_API_KEY
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# assistant = client.beta.assistants.create(
#     name='AI-ASSISTANT',
#     model='gpt-4o',
#     instructions=INSTRUCTIONS,
#     temperature=0,
#     top_p=1,
#     tools=[
#         {"type": "code_interpreter"},
#         {"type": "file_search"}
#     ],
# )

ASSISTANT_ID = AI_ASSISTANT_FOR_TELEGRAM_BOT_ID


chat_states = {}
all_threads = set()

# TODO: ### GOOGLE DOCS INITIALIZATION ###

ESTIMATES_ID = ''

docs_client = GoogleDocsService(document_id=SAMPLE_ID, credentials_path='credentials.json', token_path='token.json')
docs_client.authorize()
docs_client.build_service()

doc = docs_client.get_document(SAMPLE_ID)
layers_tab = GoogleDocsService.get_tab(doc, 'layers')
brief_tab = GoogleDocsService.get_tab(doc, 'brief')
screen_tab = GoogleDocsService.get_tab(doc, 'screen')
request_tab = GoogleDocsService.get_tab(doc, 'request')
estimates_tab = GoogleDocsService.get_tab(doc, 'estimates')
estimate_tab = GoogleDocsService.get_tab(doc, 'estimate')
sample = []
estimates = []


try:
    sample.extend(json.loads(GoogleDocsService.tab_text(layers_tab)))
    sample.extend(json.loads(GoogleDocsService.tab_text(brief_tab)))
    sample.extend(json.loads(GoogleDocsService.tab_text(screen_tab)))
    sample.extend(json.loads(GoogleDocsService.tab_text(request_tab)))
    sample.extend(json.loads(GoogleDocsService.tab_text(estimate_tab)))
    estimates = GoogleDocsService.tab_text(estimates_tab)
except Exception as json_exc:
    print(f'Failed to load tabs to json : {json_exc}')

sample_objects = {}

for fucking_obj_why_are_you_shadowed in sample:
    sample_objects[fucking_obj_why_are_you_shadowed.get('id')] = fucking_obj_why_are_you_shadowed

# TODO: ### TELEGRAM BOT INITIALIZATION ###


app = ApplicationBuilder().token(BOT_TOKEN).build()

group_timers = {}

USER_DATA_TO_CLEAR = [
    "thread",
    "code_map",
    "last_obj",
    "current_obj",
    "queue",
    "selected_options",
    "last_bot_message_id",
    "collected_messages",
    "session",
]

# TODO ### REGEX CONSTANTS INITIALIZATION ###
# special symbols: [ ] \ / ^ $ . | ? * + ( ) { }

REGEX_MAP = {
    "word": r"[A-Za-zА-Яа-яЁё]+",
    "space": r"\s+",
    "ref": r"https?:\/\/(?:[\w\-]+\.)+[a-zA-Z]{2,}(?:\/[\w\-./?%&=+#]*)?",
    "positive": r"[1-9][0-9]*",
    "int": r"-?[1-9][0-9]*|0",
    "function": r"[a-zA-Z_][a-zA-Z0-9_]*\((?:[^()]*|\((?:[^()]*|\([^()]*\))*\))*\)([\?\*\+\{\d+(,\d+)?\}]*)?"
}


REGEX_FUNCS = {}


def is_function(arg=""):
    return True if re.match(REGEX_MAP['function'], arg) else False


def REGEX_interval(args: list):
    pattern = REGEX_MAP.get(args[0].get('type'))
    for arg in args[1:]:
        pattern += r'\s*[-–—]\s*' + REGEX_MAP.get(arg.get('type'))
    return pattern


def REGEX_format(args: list):
    pattern = ''
    for arg in args:
        if arg.get('type') == 'func':
            _add = REGEX_FUNCS.get(arg.get('name'))(arg.get('args')) if REGEX_FUNCS.get(arg.get('name')) else "ERROR"
        else:
            _add = REGEX_MAP.get(arg.get('type'), 'ERROR')

        if arg.get('opt'):
            _add = f"({_add})?"
        if arg.get('from_to'):
            _add = '(' + _add + ')+{' + f'{arg.get('from_to')[0]},{arg.get('from_to')[1]}' + '}'
        if arg.get('times'):
            _add = '(' + _add + ')+{' + f'{arg.get('times')}' + '}'
        if arg.get('zero_rep'):
            _add = f'({_add})*'
        pattern += _add
    print(pattern)
    return pattern


def wrap(pattern):
    return f"^{pattern}$"


REGEX_FUNCS["interval"] = REGEX_interval
REGEX_FUNCS["format"] = REGEX_format

# TODO: ### HELPFUL  ###

refresh_lock = asyncio.Lock()
