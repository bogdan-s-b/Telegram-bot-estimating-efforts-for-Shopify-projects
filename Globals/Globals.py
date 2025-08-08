
from prime_util import *

# TODO: ### FIGMA API INITIALIZATION ###



headers = {
    'X-Figma-Token': FIGMA_API_TOKEN
}

# TODO: ### OPENAI ASSISTANT INITIALIZATION ###

INSTRUCTIONS = """

"""

CUT_PART = """
answer in format like this, replace 'something' and 'Title' with appropriate words,


### Example ###

CUSTOMER: Hi Aliaksandr,

Thanks again for the quick response — I’m excited about the potential to work together on this project.

We’re starting with a full Shopify 2.0 rebuild of 310Nutrition.com, but the goal is to create a reusable, modular architecture that we can also adapt for a few other brands we operate, including KashmereKollections.com, PlantGoods.com, and at least one more coming shortly.

That said, for now, let’s focus on quoting 310 Nutrition only — just keep in mind we’ll want to use much of the same theme structure, CRO sections, and modular logic across the other sites, so scalability and flexibility matter.

Below is the full detailed brief for the 310 project. Please review it and let me know:

If you have any questions about scope or implementation
What your estimated timeline would look like
Your proposed cost for Phase 1 (310 only)


Looking forward to your thoughts.

Best,
Tim Sharif
Founder, 310 Nutrition
tim@310nutrition.com


310 Nutrition Website Redesign Brief (Phase 1 Only)

Project Goal:
Redesign and rebuild 310Nutrition.com on Shopify 2.0 as a high-performance, conversion-optimized, modular ecommerce platform. This will include a fresh frontend design, app minimization, native tracking setup, and a fully modular Shopify 2.0 theme using native features for long-term scalability.

Scope of Work

Workshops & Strategy
UX/UI planning workshop
Technical scoping and architecture confirmation
CRO-focused content hierarchy and section layout planning

UX/UI Design (Figma)
Full redesign of 310Nutrition.com layout and interface
Modular design system in Figma with minimum 10 reusable Shopify 2.0 sections:
Hero (static + video)
Offer & bundle block
Testimonials / UGC carousel
FAQ block
Feature comparison
Review grid (Yotpo)
Ingredients/specs
Countdown timer / urgency block
CTA block
Before/after module

Page templates:
Homepage
Collection template
PDP (long-form storytelling)
About
Contact
Blog page
Modular LP template

Theme Development
Fully custom Shopify 2.0 theme using native JSON templates and schema
Mobile-first, speed optimized
Modular, low-code section architecture compatible with Shopify Customizer
Custom theme settings (color, typography, layout control)

SEO Migration & Setup
Preserve existing URLs
Implement 301 redirects where needed
Migrate metadata, H1/H2 structure, and image ALT text
Add product/blog schema and submit updated sitemap via Search Console

Tracking & Attribution
GTM and custom dataLayer setup
Integrations:
Triple Whale (primary attribution)
Google Analytics 4
Meta CAPI
Klaviyo (email tracking)
Black Crow (intent data)

Events: product view, add to cart, checkout, purchase, UTM tracking

App & Tool Audit
Keep: Klaviyo, Triple Whale, Postscripts, Black Crow AI, CartHook, Gorgias, Yotpo
Remove: Rebuy (replace natively), Magic Zoom Plus, BugSnag, ReConvert, Accessibly

Performance Optimization
Strip unused JS/CSS
Lazy-load assets, defer 3rd-party scripts
Optimize render path and minimize total payload
Rebuild Rebuy features natively with Liquid + Shopify Functions

Accessibility & Compliance
Implement WCAG 2.1 AA-compliant theme structure
Native accessibility: semantic HTML, ARIA roles, skip links, keyboard nav
Add accessibility statement and GDPR cookie compliance (replacing Accessibly)

Documentation & Handoff
Developer documentation
Screencast walkthrough of customizer
Theme admin usage guide (for internal marketers)

Testing & QA

Mobile-first QA across major breakpoints and browsers
Functionality testing (Custom sections, Add to Cart, etc.)
Shopify Customizer usability testing


Priority Outcomes:

Modular, CRO-ready Shopify 2.0 architecture
High mobile performance and clean SEO migration
Fully native implementation to reduce app bloat
Low-code flexibility for fast content updates



AI: Project Assessment and Proposal for 310 Nutrition Shopify 2.0 Rebuild:

Questions & Scope Clarification:  
- Are there any specific design inspirations or brands you admire for this redesign?
- Is a phased approach for design and development acceptable?
- What are the priority backend integrations (e.g., existing CRM, ERP systems)?

Estimated Timeline:
- Workshops & Strategy: 1-2 weeks, 20-30 hours
- UX/UI Design (Figma): 3-4 weeks, 50-70 hours
- Theme Development: 4-6 weeks, 100-150 hours
- SEO Migration & Setup: 1-2 weeks, 20-30 hours
- Tracking & Attribution Setup: 2-3 weeks, 30-40 hours
- App & Tool Audit/Removal: 1 week, 10-20 hours
- Performance Optimization: 2-3 weeks, 30-40 hours
- Accessibility & Compliance: 1 week, 10-15 hours
- Documentation & Handoff: 1 week, 10-15 hours
- Testing & QA: 2 weeks, 20-30 hours

Total Estimated Development Time: 15-21 weeks, total 300-440 hours

Proposed Cost for 310 Nutrition Website Phase 1:
- Design & Development: $40,000-$60,000
- SEO & Migration: $3,000-$5,000
- Tracking & App Auditing: $2,000-$3,500
- Performance & Compliance Optimization: $5,000-$7,000

Total Estimated Cost: $50,000-$75,000

Key Considerations:
- Focus on modular design for scalability across brands.
- Ensure all design elements align with CRO best practices.
- Optimize for mobile-first, considering current traffic trends.
- Dedicated testing phases to ensure seamless mobile and browser compatibility.
- Provide ongoing post-launch support options.

Let me know if you need modifications or further clarity.

###

"""


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
