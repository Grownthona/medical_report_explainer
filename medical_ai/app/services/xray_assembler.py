"""
xray_assembler.py
─────────────────────────────────────────────────────────────────────────────
Converts the raw output of XRayService.analyze() into the same response
shape that assemble_report() produces for lab/clinical reports.

keyword_explanation format (mirrors lab extractor convention):
    In {language} — what this condition relates to in the human body (3-5 lines).
"""

from __future__ import annotations

import logging
from services.xray_narrator import narrate_xray

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Body-context explanations per condition, per language
# Each entry explains: what part of the body is involved, what it does
# normally, and what goes wrong when this condition is detected.
# ─────────────────────────────────────────────────────────────────────────────

_KEYWORD_DEFINITIONS: dict[str, dict[str, str]] = {

    "atelectasis": {
        "en": (
            "Relates to the lungs — the organs responsible for breathing and oxygen exchange. "
            "The lungs are made of millions of tiny air sacs (alveoli) that inflate with each breath. "
            "In atelectasis, some of these sacs collapse and stop receiving air. "
            "This reduces the lungs' ability to deliver oxygen to the blood. "
            "It can affect a small section or an entire lung."
        ),
        "bn": (
            "এটি ফুসফুসের সাথে সম্পর্কিত — যে অঙ্গটি শ্বাস-প্রশ্বাস এবং অক্সিজেন বিনিময়ের জন্য দায়ী। "
            "ফুসফুস লক্ষ লক্ষ ক্ষুদ্র বায়ু থলি (অ্যালভিওলি) দিয়ে গঠিত যা প্রতিটি শ্বাসে স্ফীত হয়। "
            "অ্যাটেলেকটেসিসে এই থলিগুলির কিছু ভেঙে পড়ে এবং বায়ু গ্রহণ বন্ধ করে দেয়। "
            "এটি রক্তে অক্সিজেন সরবরাহ করার ফুসফুসের ক্ষমতা হ্রাস করে।"
        ),
        "ar": (
            "يتعلق هذا بالرئتين — العضوين المسؤولين عن التنفس وتبادل الأكسجين. "
            "تتكون الرئتان من ملايين الأكياس الهوائية الصغيرة التي تنتفخ مع كل نفس. "
            "في انخماص الرئة، تنهار بعض هذه الأكياس وتتوقف عن استقبال الهواء. "
            "يقلل ذلك من قدرة الرئتين على إيصال الأكسجين إلى الدم."
        ),
        "hi": (
            "यह फेफड़ों से संबंधित है — वे अंग जो सांस लेने और ऑक्सीजन के आदान-प्रदान के लिए जिम्मेदार हैं। "
            "फेफड़े लाखों छोटी वायु थैलियों (एल्वियोली) से बने होते हैं जो हर सांस के साथ फूलती हैं। "
            "एटेलेक्टेसिस में इनमें से कुछ थैलियां ढह जाती हैं और हवा लेना बंद कर देती हैं। "
            "इससे फेफड़ों की रक्त में ऑक्सीजन पहुंचाने की क्षमता कम हो जाती है।"
        ),
        "ur": (
            "یہ پھیپھڑوں سے متعلق ہے — وہ اعضاء جو سانس لینے اور آکسیجن کے تبادلے کے لیے ذمہ دار ہیں۔ "
            "پھیپھڑے لاکھوں چھوٹی ہوا کی تھیلیوں (الوئیولی) سے بنے ہیں جو ہر سانس کے ساتھ پھولتی ہیں۔ "
            "ایٹیلیکٹیسس میں ان میں سے کچھ تھیلیاں گر جاتی ہیں اور ہوا لینا بند کر دیتی ہیں۔ "
            "اس سے پھیپھڑوں کی خون میں آکسیجن پہنچانے کی صلاحیت کم ہو جاتی ہے۔"
        ),
    },

    "consolidation": {
        "en": (
            "Relates to the lungs and the airways that carry air into lung tissue. "
            "Normally the lungs are filled with air, allowing gas exchange with the blood. "
            "In consolidation, the air spaces fill with fluid, pus, blood, or cells instead. "
            "This is most commonly caused by pneumonia or other lung infections. "
            "The affected area can no longer participate in normal oxygen exchange."
        ),
        "bn": (
            "এটি ফুসফুস এবং ফুসফুসের টিস্যুতে বায়ু বহনকারী শ্বাসনালীর সাথে সম্পর্কিত। "
            "সাধারণত ফুসফুস বায়ু দিয়ে পূর্ণ থাকে, যা রক্তের সাথে গ্যাস বিনিময়ের অনুমতি দেয়। "
            "কনসোলিডেশনে বায়ু স্থানগুলি পরিবর্তে তরল, পুঁজ, রক্ত বা কোষ দিয়ে পূর্ণ হয়। "
            "এটি সবচেয়ে সাধারণত নিউমোনিয়া বা অন্যান্য ফুসফুসের সংক্রমণের কারণে হয়।"
        ),
        "ar": (
            "يتعلق هذا بالرئتين والمسالك الهوائية التي تحمل الهواء إلى أنسجة الرئة. "
            "عادةً تمتلئ الرئتان بالهواء مما يسمح بتبادل الغازات مع الدم. "
            "في التوطد، تمتلئ المسافات الهوائية بالسوائل أو القيح أو الدم أو الخلايا. "
            "يحدث هذا في الغالب بسبب الالتهاب الرئوي أو التهابات الرئة الأخرى."
        ),
        "hi": (
            "यह फेफड़ों और वायुमार्गों से संबंधित है जो फेफड़ों के ऊतकों में हवा ले जाते हैं। "
            "सामान्यतः फेफड़े हवा से भरे होते हैं जिससे रक्त के साथ गैस का आदान-प्रदान होता है। "
            "कंसोलिडेशन में हवा की जगह तरल, मवाद, रक्त या कोशिकाएं भर जाती हैं। "
            "यह सबसे अधिक निमोनिया या अन्य फेफड़ों के संक्रमण के कारण होता है।"
        ),
        "ur": (
            "یہ پھیپھڑوں اور ہوا کی نالیوں سے متعلق ہے جو پھیپھڑوں کے بافتوں میں ہوا لے جاتی ہیں۔ "
            "عام طور پر پھیپھڑے ہوا سے بھرے ہوتے ہیں جس سے خون کے ساتھ گیسوں کا تبادلہ ہوتا ہے۔ "
            "کنسولیڈیشن میں ہوا کی جگہ سیال، پیپ، خون یا خلیات بھر جاتے ہیں۔ "
            "یہ سب سے زیادہ نمونیا یا پھیپھڑوں کے دیگر انفیکشن کی وجہ سے ہوتا ہے۔"
        ),
    },

    "infiltration": {
        "en": (
            "Relates to the lung tissue and the tiny structures that make up the lung's surface. "
            "The lungs have a delicate lining where oxygen passes into the bloodstream. "
            "In infiltration, abnormal substances such as fluid, white blood cells, or bacteria "
            "invade this tissue and disrupt normal breathing function. "
            "It often indicates an active infection, inflammation, or early pneumonia."
        ),
        "bn": (
            "এটি ফুসফুসের টিস্যু এবং ফুসফুসের পৃষ্ঠ তৈরিকারী ক্ষুদ্র কাঠামোর সাথে সম্পর্কিত। "
            "ফুসফুসে একটি সূক্ষ্ম আস্তরণ রয়েছে যেখানে অক্সিজেন রক্তপ্রবাহে প্রবেশ করে। "
            "ইনফিলট্রেশনে তরল, শ্বেত রক্তকণিকা বা ব্যাকটেরিয়ার মতো অস্বাভাবিক পদার্থ এই টিস্যু আক্রমণ করে। "
            "এটি প্রায়শই একটি সক্রিয় সংক্রমণ বা প্রদাহ নির্দেশ করে।"
        ),
        "ar": (
            "يتعلق هذا بأنسجة الرئة والهياكل الصغيرة التي تشكل سطح الرئة. "
            "للرئتين بطانة دقيقة حيث يمر الأكسجين إلى مجرى الدم. "
            "في الارتشاح، تغزو مواد غير طبيعية مثل السوائل أو خلايا الدم البيضاء أو البكتيريا هذه الأنسجة. "
            "يشير هذا في الغالب إلى عدوى نشطة أو التهاب أو التهاب رئوي مبكر."
        ),
        "hi": (
            "यह फेफड़ों के ऊतकों और फेफड़ों की सतह बनाने वाली छोटी संरचनाओं से संबंधित है। "
            "फेफड़ों में एक नाजुक परत होती है जहां ऑक्सीजन रक्तप्रवाह में प्रवेश करती है। "
            "इनफिल्ट्रेशन में तरल, श्वेत रक्त कोशिकाएं या बैक्टीरिया इस ऊतक पर आक्रमण करते हैं। "
            "यह अक्सर सक्रिय संक्रमण, सूजन या प्रारंभिक निमोनिया का संकेत देता है।"
        ),
        "ur": (
            "یہ پھیپھڑوں کے بافتوں اور پھیپھڑوں کی سطح بنانے والے چھوٹے ڈھانچوں سے متعلق ہے۔ "
            "پھیپھڑوں میں ایک نازک پرت ہوتی ہے جہاں آکسیجن خون میں داخل ہوتی ہے۔ "
            "انفلٹریشن میں سیال، سفید خون کے خلیات یا بیکٹیریا اس بافت پر حملہ کرتے ہیں۔ "
            "یہ اکثر فعال انفیکشن، سوزش یا ابتدائی نمونیا کی علامت ہے۔"
        ),
    },

    "pneumonia": {
        "en": (
            "Relates to the lungs, specifically the air sacs (alveoli) deep inside them. "
            "These air sacs are where the body absorbs oxygen and releases carbon dioxide. "
            "In pneumonia, these sacs become inflamed and may fill with fluid or pus due to infection. "
            "This makes breathing painful and reduces the body's oxygen supply. "
            "It is one of the most common serious lung conditions worldwide."
        ),
        "bn": (
            "এটি ফুসফুসের সাথে সম্পর্কিত, বিশেষত এর গভীরে বায়ু থলি (অ্যালভিওলি)। "
            "এই বায়ু থলিগুলিই শরীর অক্সিজেন শোষণ করে এবং কার্বন ডাই অক্সাইড ছেড়ে দেয়। "
            "নিউমোনিয়ায় এই থলিগুলি সংক্রমণের কারণে ফুলে যায় এবং তরল বা পুঁজে পূর্ণ হতে পারে। "
            "এটি শ্বাস-প্রশ্বাসকে বেদনাদায়ক করে এবং শরীরের অক্সিজেন সরবরাহ কমিয়ে দেয়।"
        ),
        "ar": (
            "يتعلق هذا بالرئتين، وتحديدًا بالأكياس الهوائية (الحويصلات الهوائية) في أعماقهما. "
            "هذه الأكياس هي المكان الذي يمتص فيه الجسم الأكسجين ويطلق ثاني أكسيد الكربون. "
            "في الالتهاب الرئوي، تلتهب هذه الأكياس وقد تمتلئ بالسوائل أو القيح بسبب العدوى. "
            "يجعل ذلك التنفس مؤلمًا ويقلل من إمداد الجسم بالأكسجين."
        ),
        "hi": (
            "यह फेफड़ों से संबंधित है, विशेष रूप से उनके अंदर गहरी वायु थैलियों (एल्वियोली) से। "
            "ये वायु थैलियां वह जगह हैं जहां शरीर ऑक्सीजन अवशोषित करता है और कार्बन डाइऑक्साइड छोड़ता है। "
            "निमोनिया में ये थैलियां सूज जाती हैं और संक्रमण के कारण तरल या मवाद से भर सकती हैं। "
            "इससे सांस लेना दर्दनाक हो जाता है और शरीर की ऑक्सीजन आपूर्ति कम हो जाती है।"
        ),
        "ur": (
            "یہ پھیپھڑوں سے متعلق ہے، خاص طور پر ان کے اندر گہری ہوا کی تھیلیوں (الوئیولی) سے۔ "
            "یہ تھیلیاں وہ جگہ ہیں جہاں جسم آکسیجن جذب کرتا ہے اور کاربن ڈائی آکسائیڈ خارج کرتا ہے۔ "
            "نمونیا میں یہ تھیلیاں سوج جاتی ہیں اور انفیکشن کی وجہ سے سیال یا پیپ سے بھر سکتی ہیں۔ "
            "اس سے سانس لینا تکلیف دہ ہو جاتا ہے اور جسم کی آکسیجن کی فراہمی کم ہو جاتی ہے۔"
        ),
    },

    "pneumothorax": {
        "en": (
            "Relates to the pleural space — the narrow gap between the lung and the chest wall. "
            "Normally this space contains only a thin layer of fluid that helps the lung slide smoothly. "
            "In pneumothorax, air leaks into this space and causes the lung to partially or fully collapse. "
            "This puts pressure on the lung from outside, making breathing difficult. "
            "It can occur spontaneously or due to chest injury."
        ),
        "bn": (
            "এটি প্লুরাল স্পেসের সাথে সম্পর্কিত — ফুসফুস এবং বুকের দেওয়ালের মধ্যে সংকীর্ণ ফাঁক। "
            "সাধারণত এই স্থানে শুধুমাত্র একটি পাতলা তরল স্তর থাকে যা ফুসফুসকে মসৃণভাবে স্লাইড করতে সাহায্য করে। "
            "নিউমোথোরাক্সে বায়ু এই স্থানে প্রবেশ করে এবং ফুসফুসকে আংশিক বা সম্পূর্ণভাবে ভেঙে পড়ায়। "
            "এটি শ্বাস-প্রশ্বাসকে কঠিন করে তোলে।"
        ),
        "ar": (
            "يتعلق هذا بالفضاء الجنبي — الفجوة الضيقة بين الرئة وجدار الصدر. "
            "عادةً يحتوي هذا الفضاء على طبقة رقيقة من السائل تساعد الرئة على الانزلاق بسلاسة. "
            "في استرواح الصدر، يتسرب الهواء إلى هذا الفضاء ويتسبب في انهيار الرئة جزئيًا أو كليًا. "
            "يضغط ذلك على الرئة من الخارج مما يجعل التنفس صعبًا."
        ),
        "hi": (
            "यह फुफ्फुस स्थान से संबंधित है — फेफड़े और छाती की दीवार के बीच की संकरी जगह। "
            "सामान्यतः इस स्थान में केवल तरल की एक पतली परत होती है जो फेफड़े को सुचारू रूप से सरकने में मदद करती है। "
            "न्यूमोथोरैक्स में हवा इस स्थान में लीक होती है और फेफड़े को आंशिक या पूरी तरह से ढहा देती है। "
            "इससे बाहर से फेफड़े पर दबाव पड़ता है और सांस लेना मुश्किल हो जाता है।"
        ),
        "ur": (
            "یہ فوفیہ کی جگہ سے متعلق ہے — پھیپھڑے اور سینے کی دیوار کے درمیان تنگ خلا۔ "
            "عام طور پر اس جگہ میں صرف سیال کی ایک پتلی پرت ہوتی ہے جو پھیپھڑے کو آسانی سے سرکنے میں مدد کرتی ہے۔ "
            "نیوموتھوریکس میں ہوا اس جگہ میں داخل ہو جاتی ہے اور پھیپھڑے کو جزوی یا مکمل طور پر گرا دیتی ہے۔ "
            "اس سے باہر سے پھیپھڑے پر دباؤ پڑتا ہے اور سانس لینا مشکل ہو جاتا ہے۔"
        ),
    },

    "edema": {
        "en": (
            "Relates to the lungs and the tiny blood vessels (capillaries) surrounding them. "
            "These capillaries normally exchange oxygen and carbon dioxide with the air sacs. "
            "In pulmonary edema, fluid leaks out of these vessels and floods the lung tissue and air spaces. "
            "This is often caused by a weakened heart that cannot pump blood efficiently. "
            "It severely reduces the lungs' ability to oxygenate the blood."
        ),
        "bn": (
            "এটি ফুসফুস এবং এটি ঘিরে থাকা ক্ষুদ্র রক্তনালী (ক্যাপিলারি) সম্পর্কিত। "
            "এই ক্যাপিলারিগুলি সাধারণত বায়ু থলির সাথে অক্সিজেন এবং কার্বন ডাই অক্সাইড বিনিময় করে। "
            "পালমোনারি এডিমায় এই নালী থেকে তরল বের হয়ে ফুসফুসের টিস্যু ও বায়ু স্থান প্লাবিত করে। "
            "এটি প্রায়শই একটি দুর্বল হৃদয়ের কারণে হয় যা দক্ষতার সাথে রক্ত পাম্প করতে পারে না।"
        ),
        "ar": (
            "يتعلق هذا بالرئتين والأوعية الدموية الدقيقة (الشعيرات الدموية) المحيطة بهما. "
            "تتبادل هذه الشعيرات عادةً الأكسجين وثاني أكسيد الكربون مع الأكياس الهوائية. "
            "في وذمة الرئة، يتسرب السائل من هذه الأوعية ويفيض في أنسجة الرئة والمسافات الهوائية. "
            "غالبًا ما يحدث هذا بسبب قلب ضعيف لا يستطيع ضخ الدم بكفاءة."
        ),
        "hi": (
            "यह फेफड़ों और उनके आसपास की छोटी रक्त वाहिकाओं (कैपिलरी) से संबंधित है। "
            "ये कैपिलरी सामान्यतः वायु थैलियों के साथ ऑक्सीजन और कार्बन डाइऑक्साइड का आदान-प्रदान करती हैं। "
            "पल्मोनरी एडिमा में इन वाहिकाओं से तरल रिसकर फेफड़ों के ऊतकों और वायु स्थानों में भर जाता है। "
            "यह अक्सर कमजोर हृदय के कारण होता है जो कुशलतापूर्वक रक्त पंप नहीं कर सकता।"
        ),
        "ur": (
            "یہ پھیپھڑوں اور ان کے گرد موجود چھوٹی خون کی نالیوں (کیپیلری) سے متعلق ہے۔ "
            "یہ کیپیلری عام طور پر ہوا کی تھیلیوں کے ساتھ آکسیجن اور کاربن ڈائی آکسائیڈ کا تبادلہ کرتی ہیں۔ "
            "پلمونری ایڈیما میں ان نالیوں سے سیال رس کر پھیپھڑوں کے بافتوں اور ہوا کی جگہوں میں بھر جاتا ہے۔ "
            "یہ اکثر کمزور دل کی وجہ سے ہوتا ہے جو مؤثر طریقے سے خون پمپ نہیں کر سکتا۔"
        ),
    },

    "emphysema": {
        "en": (
            "Relates to the lungs, specifically the alveoli — the tiny balloon-like air sacs at the end of the airways. "
            "These sacs stretch and recoil with every breath, pushing stale air out efficiently. "
            "In emphysema, the walls between these sacs are destroyed, creating larger but less functional spaces. "
            "The lungs lose their elastic recoil, making it very hard to exhale completely. "
            "It is most commonly caused by long-term smoking or air pollution."
        ),
        "bn": (
            "এটি ফুসফুসের সাথে সম্পর্কিত, বিশেষত অ্যালভিওলি — শ্বাসনালীর শেষে ক্ষুদ্র বেলুনের মতো বায়ু থলি। "
            "এই থলিগুলি প্রতিটি শ্বাসে প্রসারিত হয় এবং পুরানো বায়ু দক্ষতার সাথে বের করে দেয়। "
            "এমফিসেমায় এই থলির মধ্যবর্তী দেওয়াল ধ্বংস হয়ে যায়, বড় কিন্তু কম কার্যকরী স্থান তৈরি করে। "
            "দীর্ঘমেয়াদী ধূমপান বা বায়ু দূষণ এর সবচেয়ে সাধারণ কারণ।"
        ),
        "ar": (
            "يتعلق هذا بالرئتين، وتحديدًا الحويصلات الهوائية — الأكياس الهوائية الصغيرة الشبيهة بالبالون في نهاية المسالك الهوائية. "
            "تتمدد هذه الأكياس وتنكمش مع كل نفس لدفع الهواء الفاسد للخارج. "
            "في انتفاخ الرئة، تتدمر الجدران بين هذه الأكياس مما يخلق مساحات أكبر لكن أقل فاعلية. "
            "السبب الأكثر شيوعاً هو التدخين لفترة طويلة أو تلوث الهواء."
        ),
        "hi": (
            "यह फेफड़ों से संबंधित है, विशेष रूप से एल्वियोली — वायुमार्ग के अंत में छोटी गुब्बारे जैसी वायु थैलियां। "
            "ये थैलियां हर सांस के साथ खिंचती और सिकुड़ती हैं, बासी हवा को कुशलतापूर्वक बाहर धकेलती हैं। "
            "एम्फिसीमा में इन थैलियों के बीच की दीवारें नष्ट हो जाती हैं, बड़ी लेकिन कम कार्यात्मक जगहें बनती हैं। "
            "यह सबसे अधिक लंबे समय तक धूम्रपान या वायु प्रदूषण के कारण होता है।"
        ),
        "ur": (
            "یہ پھیپھڑوں سے متعلق ہے، خاص طور پر الوئیولی — ہوا کی نالیوں کے آخر میں چھوٹی غبارے نما تھیلیاں۔ "
            "یہ تھیلیاں ہر سانس کے ساتھ پھیلتی اور سکڑتی ہیں، باسی ہوا کو مؤثر طریقے سے باہر دھکیلتی ہیں۔ "
            "ایمفیسیما میں ان تھیلیوں کے درمیان کی دیواریں تباہ ہو جاتی ہیں، بڑی لیکن کم فعال جگہیں بنتی ہیں۔ "
            "یہ سب سے زیادہ طویل مدتی سگریٹ نوشی یا فضائی آلودگی کی وجہ سے ہوتا ہے۔"
        ),
    },

    "fibrosis": {
        "en": (
            "Relates to the lung tissue and its supporting framework of connective tissue. "
            "Healthy lung tissue is soft and flexible, allowing the lungs to expand and contract freely. "
            "In fibrosis, repeated injury or inflammation causes scar tissue to replace normal lung tissue. "
            "This makes the lungs stiff and thick, reducing their capacity to take in oxygen. "
            "Over time, it progressively limits breathing and oxygen exchange."
        ),
        "bn": (
            "এটি ফুসফুসের টিস্যু এবং সংযোগকারী টিস্যুর সহায়ক কাঠামোর সাথে সম্পর্কিত। "
            "সুস্থ ফুসফুসের টিস্যু নরম এবং নমনীয়, যা ফুসফুসকে অবাধে প্রসারিত ও সংকুচিত হতে দেয়। "
            "ফাইব্রোসিসে বারবার আঘাত বা প্রদাহ স্বাভাবিক টিস্যুর জায়গায় দাগ টিস্যু তৈরি করে। "
            "এটি ফুসফুসকে শক্ত ও ঘন করে এবং অক্সিজেন গ্রহণের ক্ষমতা হ্রাস করে।"
        ),
        "ar": (
            "يتعلق هذا بأنسجة الرئة وإطارها الداعم من النسيج الضام. "
            "أنسجة الرئة السليمة ناعمة ومرنة مما يسمح للرئتين بالتمدد والانقباض بحرية. "
            "في التليف، يتسبب الإصابة المتكررة أو الالتهاب في استبدال أنسجة الرئة الطبيعية بنسيج ندبي. "
            "يجعل ذلك الرئتين صلبتين وسميكتين مما يقلل قدرتهما على استيعاب الأكسجين."
        ),
        "hi": (
            "यह फेफड़ों के ऊतकों और संयोजी ऊतक के सहायक ढांचे से संबंधित है। "
            "स्वस्थ फेफड़ों के ऊतक नरम और लचीले होते हैं, जिससे फेफड़े स्वतंत्र रूप से फैल और सिकुड़ सकते हैं। "
            "फाइब्रोसिस में बार-बार चोट या सूजन से सामान्य ऊतक की जगह निशान ऊतक बन जाता है। "
            "इससे फेफड़े सख्त और मोटे हो जाते हैं और ऑक्सीजन लेने की क्षमता कम हो जाती है।"
        ),
        "ur": (
            "یہ پھیپھڑوں کے بافتوں اور کنیکٹیو ٹشو کے معاون ڈھانچے سے متعلق ہے۔ "
            "صحت مند پھیپھڑوں کے بافتے نرم اور لچکدار ہوتے ہیں جو پھیپھڑوں کو آزادانہ پھیلنے اور سکڑنے دیتے ہیں۔ "
            "فائبروسس میں بار بار چوٹ یا سوزش سے نارمل بافتوں کی جگہ داغ کے بافتے بن جاتے ہیں۔ "
            "اس سے پھیپھڑے سخت اور موٹے ہو جاتے ہیں اور آکسیجن لینے کی صلاحیت کم ہو جاتی ہے۔"
        ),
    },

    "pleural effusion": {
        "en": (
            "Relates to the pleura — the two-layered membrane that surrounds each lung and lines the chest cavity. "
            "Normally a small amount of fluid between these layers helps the lungs move smoothly during breathing. "
            "In pleural effusion, excess fluid builds up in this space and compresses the lung from outside. "
            "This can be caused by heart failure, infection, cancer, or kidney disease. "
            "It reduces the space available for the lung to expand and causes breathlessness."
        ),
        "bn": (
            "এটি প্লুরার সাথে সম্পর্কিত — দ্বি-স্তরীয় ঝিল্লি যা প্রতিটি ফুসফুসকে ঘিরে থাকে। "
            "সাধারণত এই স্তরগুলির মধ্যে অল্প পরিমাণ তরল ফুসফুসকে মসৃণভাবে নড়াচড়া করতে সাহায্য করে। "
            "প্লুরাল ইফিউশনে এই স্থানে অতিরিক্ত তরল জমে ফুসফুসকে বাইরে থেকে সংকুচিত করে। "
            "এটি হৃদরোগ, সংক্রমণ, ক্যান্সার বা কিডনি রোগের কারণে হতে পারে।"
        ),
        "ar": (
            "يتعلق هذا بالغشاء الجنبي — الغشاء ذو الطبقتين الذي يحيط بكل رئة ويبطن تجويف الصدر. "
            "عادةً تساعد كمية صغيرة من السائل بين هذه الطبقات الرئتين على التحرك بسلاسة أثناء التنفس. "
            "في الانصباب الجنبي، يتراكم السائل الزائد في هذا الفضاء ويضغط على الرئة من الخارج. "
            "يمكن أن يحدث هذا بسبب قصور القلب أو العدوى أو السرطان أو أمراض الكلى."
        ),
        "hi": (
            "यह फुफ्फुस झिल्ली (प्लुरा) से संबंधित है — दो परतों वाली झिल्ली जो प्रत्येक फेफड़े को घेरती है। "
            "सामान्यतः इन परतों के बीच थोड़ा तरल फेफड़ों को सांस लेते समय सुचारू रूप से चलने में मदद करता है। "
            "प्लूरल एफ्यूजन में इस स्थान में अधिक तरल जमा होकर फेफड़े को बाहर से दबाता है। "
            "यह हृदय विफलता, संक्रमण, कैंसर या किडनी रोग के कारण हो सकता है।"
        ),
        "ur": (
            "یہ فوفیہ (پلورا) سے متعلق ہے — دو پرتوں والی جھلی جو ہر پھیپھڑے کو گھیرتی ہے۔ "
            "عام طور پر ان پرتوں کے درمیان تھوڑا سیال پھیپھڑوں کو سانس لیتے وقت آسانی سے حرکت کرنے میں مدد کرتا ہے۔ "
            "پلورل ایفیوژن میں اس جگہ میں زیادہ سیال جمع ہو کر پھیپھڑے کو باہر سے دباتا ہے۔ "
            "یہ دل کی ناکامی، انفیکشن، کینسر یا گردے کی بیماری کی وجہ سے ہو سکتا ہے۔"
        ),
    },

    "cardiomegaly": {
        "en": (
            "Relates to the heart — the muscular organ that pumps blood throughout the entire body. "
            "A normal adult heart is roughly the size of a fist and sits in the centre of the chest. "
            "In cardiomegaly, the heart muscle has enlarged beyond its normal size, visible on X-ray. "
            "This can be caused by high blood pressure, heart valve problems, or heart failure. "
            "An enlarged heart has to work harder to pump blood, which can worsen over time."
        ),
        "bn": (
            "এটি হৃদয়ের সাথে সম্পর্কিত — পেশীবহুল অঙ্গ যা সমগ্র শরীরে রক্ত পাম্প করে। "
            "একটি স্বাভাবিক প্রাপ্তবয়স্ক হৃদয় একটি মুষ্টির আকারের এবং বুকের মাঝখানে অবস্থিত। "
            "কার্ডিওমেগালিতে হৃদয়ের পেশী স্বাভাবিক আকারের বাইরে বড় হয়ে যায়। "
            "এটি উচ্চ রক্তচাপ, হার্টের ভাল্বের সমস্যা বা হার্ট ফেইলিউরের কারণে হতে পারে।"
        ),
        "ar": (
            "يتعلق هذا بالقلب — العضو العضلي الذي يضخ الدم في جميع أنحاء الجسم. "
            "يبلغ حجم قلب البالغ السليم تقريبًا حجم القبضة ويقع في وسط الصدر. "
            "في تضخم القلب، تتضخم عضلة القلب إلى ما هو أكبر من حجمها الطبيعي ويظهر ذلك في الأشعة. "
            "يمكن أن يحدث هذا بسبب ارتفاع ضغط الدم أو مشاكل صمامات القلب أو قصور القلب."
        ),
        "hi": (
            "यह हृदय से संबंधित है — मांसपेशीय अंग जो पूरे शरीर में रक्त पंप करता है। "
            "एक सामान्य वयस्क हृदय लगभग एक मुट्ठी के आकार का होता है और छाती के केंद्र में स्थित होता है। "
            "कार्डियोमेगाली में हृदय की मांसपेशी अपने सामान्य आकार से बड़ी हो जाती है, जो X-ray पर दिखती है। "
            "यह उच्च रक्तचाप, हृदय वाल्व की समस्याओं या हृदय विफलता के कारण हो सकता है।"
        ),
        "ur": (
            "یہ دل سے متعلق ہے — عضلاتی عضو جو پورے جسم میں خون پمپ کرتا ہے۔ "
            "ایک نارمل بالغ دل تقریباً مٹھی کے برابر ہوتا ہے اور سینے کے وسط میں واقع ہوتا ہے۔ "
            "کارڈیومیگالی میں دل کا پٹھا اپنے نارمل سائز سے بڑا ہو جاتا ہے جو ایکسرے پر نظر آتا ہے۔ "
            "یہ ہائی بلڈ پریشر، دل کے والو کی خرابی یا دل کی ناکامی کی وجہ سے ہو سکتا ہے۔"
        ),
    },

    "fracture": {
        "en": (
            "Relates to the bones of the chest — most commonly the ribs, collarbone (clavicle), or breastbone (sternum). "
            "The rib cage protects the lungs and heart and supports the muscles used for breathing. "
            "A fracture means one or more of these bones has cracked or completely broken. "
            "This can be caused by trauma, a fall, or in some cases weakened bones (osteoporosis). "
            "Rib fractures can be painful and, if severe, may affect breathing."
        ),
        "bn": (
            "এটি বুকের হাড়ের সাথে সম্পর্কিত — সাধারণত পাঁজর, কলারবোন বা বুকের হাড়। "
            "পাঁজরের খাঁচা ফুসফুস ও হৃদয়কে রক্ষা করে এবং শ্বাস-প্রশ্বাসের পেশীকে সমর্থন করে। "
            "ফ্র্যাকচার মানে এই হাড়গুলির একটি বা একাধিক ফেটে গেছে বা সম্পূর্ণ ভেঙে গেছে। "
            "এটি আঘাত, পতন বা দুর্বল হাড় (অস্টিওপোরোসিস) থেকে হতে পারে।"
        ),
        "ar": (
            "يتعلق هذا بعظام الصدر — وعادةً ما تكون الأضلاع أو عظمة الترقوة أو عظمة القص. "
            "يحمي القفص الصدري الرئتين والقلب ويدعم العضلات المستخدمة في التنفس. "
            "الكسر يعني أن عظمة أو أكثر قد تشققت أو كُسرت تمامًا. "
            "يمكن أن يحدث هذا بسبب الصدمة أو السقوط أو في بعض الحالات ضعف العظام."
        ),
        "hi": (
            "यह छाती की हड्डियों से संबंधित है — आमतौर पर पसलियां, कॉलरबोन या ब्रेस्टबोन। "
            "पसली का पिंजरा फेफड़ों और हृदय की रक्षा करता है और सांस लेने में उपयोग की जाने वाली मांसपेशियों को सहारा देता है। "
            "फ्रैक्चर का मतलब है इनमें से एक या अधिक हड्डियां टूट या दरक गई हैं। "
            "यह आघात, गिरने या कमजोर हड्डियों (ऑस्टियोपोरोसिस) के कारण हो सकता है।"
        ),
        "ur": (
            "یہ سینے کی ہڈیوں سے متعلق ہے — عام طور پر پسلیاں، کالر بون یا سینے کی ہڈی۔ "
            "پسلیوں کا پنجرہ پھیپھڑوں اور دل کی حفاظت کرتا ہے اور سانس لینے میں استعمال ہونے والے پٹھوں کو سہارا دیتا ہے۔ "
            "فریکچر کا مطلب ہے کہ ان میں سے ایک یا زیادہ ہڈیاں ٹوٹ یا دڑک گئی ہیں۔ "
            "یہ چوٹ، گرنے یا کمزور ہڈیوں (آسٹیوپوروسس) کی وجہ سے ہو سکتا ہے۔"
        ),
    },

    "mass": {
        "en": (
            "Relates to any organ or tissue inside the chest where an abnormal growth has formed. "
            "In chest X-ray reporting, a mass is a growth larger than 3 cm detected in the lung or chest cavity. "
            "Masses can develop in lung tissue, lymph nodes, or the structures between the lungs. "
            "They can be benign (non-cancerous) or malignant (cancerous) — further tests are needed to confirm. "
            "Early detection and follow-up imaging are important for proper evaluation."
        ),
        "bn": (
            "এটি বুকের ভেতরে যেকোনো অঙ্গ বা টিস্যুর সাথে সম্পর্কিত যেখানে একটি অস্বাভাবিক বৃদ্ধি তৈরি হয়েছে। "
            "বুকের এক্স-রে রিপোর্টে, একটি মাস হলো ৩ সেমির বেশি বড় বৃদ্ধি যা ফুসফুস বা বুকের গহ্বরে সনাক্ত হয়। "
            "এটি সৌম্য (ক্যান্সারবিহীন) বা ম্যালিগন্যান্ট (ক্যান্সারজনিত) হতে পারে। "
            "সঠিক মূল্যায়নের জন্য আরও পরীক্ষা প্রয়োজন।"
        ),
        "ar": (
            "يتعلق هذا بأي عضو أو نسيج داخل الصدر حيث تشكّل نمو غير طبيعي. "
            "في تقارير أشعة الصدر، الكتلة هي نمو أكبر من 3 سم يُكتشف في الرئة أو تجويف الصدر. "
            "يمكن أن تتطور الكتل في أنسجة الرئة أو الغدد الليمفاوية أو الهياكل بين الرئتين. "
            "يمكن أن تكون حميدة أو خبيثة — وتحتاج إلى مزيد من الفحوصات للتأكد."
        ),
        "hi": (
            "यह छाती के अंदर किसी भी अंग या ऊतक से संबंधित है जहां एक असामान्य वृद्धि बन गई है। "
            "छाती के X-ray में, मास एक ऐसी वृद्धि है जो 3 सेमी से बड़ी होती है और फेफड़े या छाती की गुहा में पाई जाती है। "
            "यह सौम्य (गैर-कैंसरयुक्त) या घातक (कैंसरयुक्त) हो सकता है। "
            "उचित मूल्यांकन के लिए आगे के परीक्षण आवश्यक हैं।"
        ),
        "ur": (
            "یہ سینے کے اندر کسی بھی عضو یا بافت سے متعلق ہے جہاں غیر معمولی بڑھوتری ہوئی ہو۔ "
            "سینے کے ایکسرے میں، ماس ایک ایسی بڑھوتری ہے جو 3 سینٹی میٹر سے بڑی ہو اور پھیپھڑوں یا سینے کی گہا میں پائی جائے۔ "
            "یہ سومی (غیر سرطانی) یا مہلک (سرطانی) ہو سکتی ہے۔ "
            "مناسب جانچ کے لیے مزید ٹیسٹ ضروری ہیں۔"
        ),
    },

    "nodule": {
        "en": (
            "Relates to the lung tissue where a small, rounded area of abnormal growth has formed. "
            "A nodule is smaller than 3 cm and can appear in one or both lungs on a chest X-ray. "
            "Most lung nodules are benign and caused by old infections, scar tissue, or inflammation. "
            "However, some can indicate early-stage lung cancer, so follow-up imaging is recommended. "
            "The size, shape, and density of the nodule guide the doctor's next steps."
        ),
        "bn": (
            "এটি ফুসফুসের টিস্যুর সাথে সম্পর্কিত যেখানে অস্বাভাবিক বৃদ্ধির একটি ছোট, গোলাকার অংশ তৈরি হয়েছে। "
            "একটি নডিউল ৩ সেমির ছোট এবং বুকের এক্স-রেতে এক বা উভয় ফুসফুসে দেখা যেতে পারে। "
            "বেশিরভাগ ফুসফুসের নডিউল সৌম্য এবং পুরানো সংক্রমণ বা দাগ টিস্যু থেকে হয়। "
            "তবে কিছু প্রাথমিক পর্যায়ের ফুসফুসের ক্যান্সার নির্দেশ করতে পারে।"
        ),
        "ar": (
            "يتعلق هذا بأنسجة الرئة حيث تشكّلت منطقة صغيرة ومستديرة من النمو غير الطبيعي. "
            "العقيدة أصغر من 3 سم ويمكن أن تظهر في رئة أو كلتيهما في أشعة الصدر. "
            "معظم عقيدات الرئة حميدة وناجمة عن التهابات قديمة أو نسيج ندبي أو التهاب. "
            "ومع ذلك قد تشير بعضها إلى سرطان رئة في مرحلة مبكرة."
        ),
        "hi": (
            "यह फेफड़ों के ऊतकों से संबंधित है जहां असामान्य वृद्धि का एक छोटा, गोलाकार क्षेत्र बना है। "
            "एक नोड्यूल 3 सेमी से छोटा होता है और छाती के X-ray पर एक या दोनों फेफड़ों में दिख सकता है। "
            "अधिकांश फेफड़ों के नोड्यूल सौम्य होते हैं और पुराने संक्रमण या निशान ऊतक से होते हैं। "
            "हालांकि कुछ प्रारंभिक चरण के फेफड़ों के कैंसर का संकेत दे सकते हैं।"
        ),
        "ur": (
            "یہ پھیپھڑوں کے بافتوں سے متعلق ہے جہاں غیر معمولی بڑھوتری کا ایک چھوٹا، گول علاقہ بنا ہو۔ "
            "ایک نوڈول 3 سینٹی میٹر سے چھوٹا ہوتا ہے اور سینے کے ایکسرے پر ایک یا دونوں پھیپھڑوں میں نظر آ سکتا ہے۔ "
            "زیادہ تر پھیپھڑوں کے نوڈول سومی ہوتے ہیں اور پرانے انفیکشن یا داغ کے بافتوں سے ہوتے ہیں۔ "
            "تاہم کچھ ابتدائی مرحلے کے پھیپھڑوں کے سرطان کی علامت ہو سکتے ہیں۔"
        ),
    },

    "no finding": {
        "en": (
            "Relates to the overall chest structures — lungs, heart, ribs, and major blood vessels. "
            "A normal chest X-ray shows clear lungs, a heart of normal size, and intact bony structures. "
            "No finding means the AI model did not detect any significant abnormality in any of these areas. "
            "This is a reassuring result, though AI analysis is not a substitute for a doctor's review. "
            "Routine follow-up with your physician is still recommended."
        ),
        "bn": (
            "এটি সামগ্রিক বুকের কাঠামোর সাথে সম্পর্কিত — ফুসফুস, হৃদয়, পাঁজর এবং প্রধান রক্তনালী। "
            "একটি স্বাভাবিক বুকের এক্স-রেতে স্বচ্ছ ফুসফুস, স্বাভাবিক আকারের হৃদয় দেখা যায়। "
            "নো ফাইন্ডিং মানে AI মডেল এই এলাকাগুলিতে কোনো উল্লেখযোগ্য অস্বাভাবিকতা সনাক্ত করেনি। "
            "এটি একটি আশ্বস্তকারী ফলাফল, তবে ডাক্তারের পর্যালোচনা তখনও প্রয়োজন।"
        ),
        "ar": (
            "يتعلق هذا بهياكل الصدر الكلية — الرئتين والقلب والأضلاع والأوعية الدموية الرئيسية. "
            "تُظهر أشعة الصدر الطبيعية رئتين صافيتين وقلبًا بحجم طبيعي وهياكل عظمية سليمة. "
            "لا يوجد اكتشاف يعني أن نموذج الذكاء الاصطناعي لم يكتشف أي شذوذ كبير في هذه المناطق. "
            "هذه نتيجة مطمئنة، وإن كانت مراجعة الطبيب لا تزال ضرورية."
        ),
        "hi": (
            "यह समग्र छाती संरचनाओं से संबंधित है — फेफड़े, हृदय, पसलियां और प्रमुख रक्त वाहिकाएं। "
            "एक सामान्य छाती X-ray स्पष्ट फेफड़े, सामान्य आकार का हृदय दिखाता है। "
            "नो फाइंडिंग का अर्थ है AI मॉडल ने इन क्षेत्रों में कोई महत्वपूर्ण असामान्यता नहीं पाई। "
            "यह एक आश्वस्त करने वाला परिणाम है, हालांकि डॉक्टर की समीक्षा अभी भी अनुशंसित है।"
        ),
        "ur": (
            "یہ مجموعی سینے کے ڈھانچوں سے متعلق ہے — پھیپھڑے، دل، پسلیاں اور بڑی خون کی نالیاں۔ "
            "ایک نارمل سینے کا ایکسرے صاف پھیپھڑے اور نارمل سائز کا دل دکھاتا ہے۔ "
            "نو فائنڈنگ کا مطلب ہے AI ماڈل نے ان علاقوں میں کوئی اہم غیر معمولی بات نہیں پائی۔ "
            "یہ ایک اطمینان بخش نتیجہ ہے، لیکن ڈاکٹر کا جائزہ پھر بھی ضروری ہے۔"
        ),
    },
}

# Fallback for conditions not in the dictionary
_FALLBACK: dict[str, str] = {
    "en": (
        "This is a radiological finding detected in the chest X-ray. "
        "It relates to the structures inside the chest including the lungs, heart, or surrounding tissues. "
        "The AI model identified this as a notable area requiring attention. "
        "Please consult your doctor for a full explanation of what this finding means for your health."
    ),
    "bn": (
        "এটি বুকের এক্স-রেতে সনাক্ত একটি রেডিওলজিক্যাল ফলাফল। "
        "এটি বুকের ভেতরের কাঠামোর সাথে সম্পর্কিত যার মধ্যে ফুসফুস, হৃদয় বা আশেপাশের টিস্যু রয়েছে। "
        "এই ফলাফল আপনার স্বাস্থ্যের জন্য কী অর্থ বহন করে তা জানতে আপনার ডাক্তারের সাথে পরামর্শ করুন।"
    ),
    "ar": (
        "هذه نتيجة إشعاعية تم اكتشافها في أشعة الصدر. "
        "تتعلق بالهياكل داخل الصدر بما في ذلك الرئتين والقلب أو الأنسجة المحيطة. "
        "يرجى استشارة طبيبك للحصول على شرح كامل لما تعنيه هذه النتيجة لصحتك."
    ),
    "hi": (
        "यह छाती के X-ray में पाया गया एक रेडियोलॉजिकल निष्कर्ष है। "
        "यह छाती के अंदर की संरचनाओं से संबंधित है जिसमें फेफड़े, हृदय या आसपास के ऊतक शामिल हैं। "
        "यह निष्कर्ष आपके स्वास्थ्य के लिए क्या मायने रखता है, इसके लिए अपने डॉक्टर से परामर्श करें।"
    ),
    "ur": (
        "یہ سینے کے ایکسرے میں پایا گیا ایک ریڈیولوجیکل نتیجہ ہے۔ "
        "یہ سینے کے اندر کے ڈھانچوں سے متعلق ہے جن میں پھیپھڑے، دل یا آس پاس کے بافتے شاملیں۔ "
        "یہ نتیجہ آپ کی صحت کے لیے کیا معنی رکھتا ہے، اس کے لیے اپنے ڈاکٹر سے مشورہ کریں۔"
    ),
}


def _get_keyword_definition(condition: str, language: str = "en") -> str:
    """Return a body-context explanation for a condition in the given language."""
    key  = condition.strip().lower()
    lang = language if language in ("en", "bn", "ar", "hi", "ur") else "en"

    # Direct lookup
    if key in _KEYWORD_DEFINITIONS:
        return _KEYWORD_DEFINITIONS[key].get(lang, _KEYWORD_DEFINITIONS[key]["en"])

    # Partial match
    for known_key, translations in _KEYWORD_DEFINITIONS.items():
        if known_key in key or key in known_key:
            return translations.get(lang, translations["en"])

    # Fallback
    return _FALLBACK.get(lang, _FALLBACK["en"])


def _finding_to_status(prob: float) -> str:
    if prob >= 50: return "High"
    if prob >= 20: return "Low"
    return "Normal"


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def assemble_xray_report(result: dict, language: str = "en") -> dict:
    """
    Convert XRayService.analyze() output → unified report shape.

    Args:
        result:   dict returned by XRayService.analyze()
        language: response language code (en, bn, ar, hi, ur)

    Returns:
        Dict with the same top-level keys as assemble_report():
        is_multi_patient, is_mixed, document_type, patient,
        report, sections, summary, language
    """
    if not result.get("success"):
        raise RuntimeError("X-ray model returned unsuccessful result.")

    top_findings: list[dict] = result.get("top_findings", [])

    # ── Build tests_analysis ──────────────────────────────────────────────────
    tests_analysis: list[dict] = [
        {
            "test_name":       f["condition"],
            "value":           f"{f['probability']}%",
            "unit":            "probability",
            "reference_range": "< 10%",
            "status":          _finding_to_status(f["probability"]),
            # What this condition relates to in the human body (3-5 lines, in language)
            "keyword_explanation": _get_keyword_definition(f["condition"], language),
            # What this specific finding means for the patient — filled after narration
            "result_explanation":  "",
        }
        for f in top_findings
    ]

    # ── Narration ─────────────────────────────────────────────────────────────
    predictions: list[dict] = [
        {"label": f["condition"], "probability": round(f["probability"] / 100, 4)}
        for f in top_findings
    ]
    narration: dict = narrate_xray(predictions, language=language)

    narration_findings: str = narration.get("findings", "")
    for row in tests_analysis:
        row["result_explanation"] = narration_findings

    # ── Summary ───────────────────────────────────────────────────────────────
    abnormal = [t for t in tests_analysis if t["status"] in ("High", "Low")]
    critical = [t for t in tests_analysis if t["status"] == "High"]
    summary  = {
        "total_tests":    len(tests_analysis),
        "abnormal_count": len(abnormal),
        "critical_count": len(critical),
        "has_critical":   len(critical) > 0,
    }

    # ── Risk level ────────────────────────────────────────────────────────────
    if any(t["status"] == "High" for t in tests_analysis):
        risk_level = "High"
    elif any(t["status"] == "Low" for t in tests_analysis):
        risk_level = "Medium"
    else:
        risk_level = "Low"

    return {
        "is_multi_patient": False,
        "is_mixed":         False,

        "document_type": {
            "category":   "RADIOLOGY",
            "sub_type":   "CHEST_XRAY",
            "confidence": "HIGH",
            "is_mixed":   False,
        },

        "patient": {
            "name":            None,
            "age_years":       None,
            "gender":          "unknown",
            "report_type":     "Chest X-Ray",
            "collection_date": None,
        },

        "report": {
            "summary":           narration.get("findings", ""),
            "voice_explanation": narration.get("voice_explanation", ""),
            "tests_analysis":    tests_analysis,
            "risk_level":        risk_level,
            "advice":            narration.get("advice", ""),
            "model":             result.get("model", ""),
            "disclaimer":        result.get("disclaimer", ""),
            "all_findings":      result.get("findings", []),
        },

        "sections": {},
        "summary":  summary,
        "language": language,
    }