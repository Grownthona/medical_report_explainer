export const MOCK_SAMPLES = {
  // 1. For Multiple image file (Mixed Report)
  MULTIPLE_IMAGE_MIXED: {
    "is_mixed": true,
    "document_type": {
        "category": "LAB + IMAGING",
        "sub_type": "MIXED",
        "confidence": "MEDIUM",
        "is_mixed": true
    },
    "patient": {
        "name": "GRANTHANA RAHMAN",
        "age_years": 24,
        "gender": "female",
        "report_type": "CBC",
        "collection_date": "2024-11-05",
        "referred_by": "DR.MD.AZIZUL KAHHAR",
        "lab_no": "22411208208",
        "invoice_no": "D2411127699"
    },
    "sections": {
        "LAB": [
            {
                "summary": "এই মেডিকেল রিপোর্টে রক্ত ​​পরীক্ষা এবং রেডিওলজি পরীক্ষার ফলাফল রয়েছে। রক্ত ​​পরীক্ষায়, ESR (ইরিথ্রোসাইট সেডিমেন্টেশন রেট) স্বাভাবিকের চেয়ে বেশি পাওয়া গেছে। অন্যান্য রক্তকণিকার প্যারামিটারগুলি (যেমন WBC, RBC, প্লেটলেট) সাধারণত স্বাভাবিক সীমার মধ্যে রয়েছে। রেডিওলজি রিপোর্টে ডান দিকের ফুসফুসের গোড়ায় প্লুরাল রিঅ্যাকশন এবং ছোট ঘন অস্বচ্ছতা (opacities) দেখা গেছে। এই ফলাফলগুলি ফুসফুসে বা প্লুরাতে প্রদাহ বা অন্য কোনো সমস্যার ইঙ্গিত দিতে পারে।",
                "voice_explanation": "আপনার মেডিকেল রিপোর্টে দেখা যাচ্ছে যে আপনার ESR স্বাভাবিকের চেয়ে বেশি। এটি শরীরে প্রদাহের একটি সাধারণ সূচক। এছাড়াও, আপনার বুকের এক্স-রে বা ইমেজিং রিপোর্টে ডান দিকের ফুসফুসের গোড়ায় কিছু অস্বাভাবিকতা যেমন প্লুরাল রিঅ্যাকশন এবং ছোট অস্বচ্ছতা দেখা গেছে। এই দুটি ফলাফল একসাথে ফুসফুসে বা প্লুরাতে কোনো সমস্যা নির্দেশ করতে পারে। অন্যান্য রক্ত ​​পরীক্ষার ফলাফলগুলি সাধারণত স্বাভাবিক সীমার মধ্যে রয়েছে। এই বিষয়ে একজন ডাক্তারের সাথে বিস্তারিত আলোচনা করা অত্যন্ত গুরুত্বপূর্ণ।",
                "tests_analysis": [
                    {
                        "test_name": "ESR (Erythrocyte Sedimentation Rate)",
                        "value": 47.0,
                        "unit": "mm in 1st hr.",
                        "reference_range": "Female: 0-20 mm in 1st hr.",
                        "status": "High",
                        "keyword_explanation": "ESR হলো একটি পরীক্ষা যা রক্তে লোহিত রক্তকণিকা কত দ্রুত একটি টেস্ট টিউবের নিচে জমা হয় তা পরিমাপ করে। এটি শরীরে প্রদাহ বা সংক্রমণের একটি সাধারণ সূচক।",
                        "result_explanation": "আপনার ESR স্বাভাবিকের চেয়ে বেশি, যা শরীরে প্রদাহ বা সংক্রমণের উপস্থিতি নির্দেশ করতে পারে। একজন ডাক্তারের পরামর্শ নিন।"
                    },
                    {
                        "test_name": "Total Count (WBC)",
                        "value": 10.74,
                        "unit": "X10^9/L",
                        "reference_range": "04.00-11.00 X10^9/L",
                        "status": "Normal",
                        "keyword_explanation": "WBC বা শ্বেত রক্তকণিকা শরীরের রোগ প্রতিরোধ ব্যবস্থার অংশ। এটি সংক্রমণ এবং প্রদাহের বিরুদ্ধে লড়াই করে।",
                        "result_explanation": "আপনার শ্বেত রক্তকণিকার সংখ্যা স্বাভাবিক সীমার মধ্যে রয়েছে।"
                    },
                    {
                        "test_name": "RBC (Red Blood Cell)",
                        "value": 4.76,
                        "unit": "X10^12/L",
                        "reference_range": "Female: 3.8-5.0 x10^12/L",
                        "status": "Normal",
                        "keyword_explanation": "RBC বা লোহিত রক্তকণিকা ফুসফুস থেকে শরীরের অন্যান্য অংশে অক্সিজেন বহন করে।",
                        "result_explanation": "আপনার লোহিত রক্তকণিকার সংখ্যা স্বাভাবিক সীমার মধ্যে রয়েছে।"
                    },
                    {
                        "test_name": "Haemoglobin",
                        "value": "Unknown",
                        "unit": "g/dL",
                        "reference_range": "F:11.5-15.5 g/d",
                        "status": "Unknown",
                        "keyword_explanation": "হিমোগ্লোবিন হলো লোহিত রক্তকণিকায় থাকা একটি প্রোটিন যা অক্সিজেন বহন করে।",
                        "result_explanation": "রিপোর্টে হিমোগ্লোবিনের মান স্পষ্টভাবে উল্লেখ করা হয়নি বা শনাক্ত করা যায়নি। একজন ডাক্তারের পরামর্শ নিন।"
                    },
                    {
                        "test_name": "PCV/HCT (Packed Cell Volume / Hematocrit)",
                        "value": 39.4,
                        "unit": "%",
                        "reference_range": "F:37-47%",
                        "status": "Normal",
                        "keyword_explanation": "PCV বা হেমাটোক্রিট হলো রক্তে লোহিত রক্তকণিকার আয়তনের শতাংশ।",
                        "result_explanation": "আপনার PCV/HCT স্বাভাবিক সীমার মধ্যে রয়েছে।"
                    },
                    {
                        "test_name": "MCV (Mean Corpuscular Volume)",
                        "value": 82.8,
                        "unit": "fL",
                        "reference_range": "Unknown",
                        "status": "Normal",
                        "keyword_explanation": "MCV হলো একটি লোহিত রক্তকণিকার গড় আয়তন। এটি রক্তাল্পতার ধরন নির্ণয়ে সাহায্য করে।",
                        "result_explanation": "আপনার MCV মান সাধারণত স্বাভাবিক সীমার মধ্যে পড়ে, যদিও রিপোর্টে নির্দিষ্ট রেফারেন্স রেঞ্জ দেওয়া হয়নি।"
                    },
                    {
                        "test_name": "MCH (Mean Corpuscular Hemoglobin)",
                        "value": 33.5,
                        "unit": "g/dL",
                        "reference_range": "31.5-34.5 g/dL",
                        "status": "Normal",
                        "keyword_explanation": "MCH হলো একটি লোহিত রক্তকণিকায় হিমোগ্লোবিনের গড় পরিমাণ।",
                        "result_explanation": "আপনার MCH মান রিপোর্টে উল্লিখিত রেফারেন্স রেঞ্জের মধ্যে রয়েছে, যা স্বাভাবিক।"
                    },
                    {
                        "test_name": "MPV (Mean Platelet Volume)",
                        "value": 10.0,
                        "unit": "fL",
                        "reference_range": "Unknown",
                        "status": "Normal",
                        "keyword_explanation": "MPV হলো প্লেটলেটের গড় আয়তন। এটি প্লেটলেট উৎপাদন এবং ধ্বংসের হার সম্পর্কে ধারণা দেয়।",
                        "result_explanation": "আপনার MPV মান সাধারণত স্বাভাবিক সীমার মধ্যে পড়ে, যদিও রিপোর্টে নির্দিষ্ট রেফারেন্স রেঞ্জ দেওয়া হয়নি।"
                    },
                    {
                        "test_name": "Platelets",
                        "value": 367.0,
                        "unit": "X10^9/L",
                        "reference_range": "150-450 X10^9/L",
                        "status": "Normal",
                        "keyword_explanation": "প্লেটলেট হলো ছোট রক্তকণিকা যা রক্ত ​​জমাট বাঁধতে এবং রক্তপাত বন্ধ করতে সাহায্য করে।",
                        "result_explanation": "আপনার প্লেটলেটের সংখ্যা স্বাভাবিক সীমার মধ্যে রয়েছে।"
                    },
                    {
                        "test_name": "RDW-SD (Red Cell Distribution Width - Standard Deviation)",
                        "value": 40.2,
                        "unit": "%",
                        "reference_range": "Unknown",
                        "status": "Unknown",
                        "keyword_explanation": "RDW-SD লোহিত রক্তকণিকার আকারের ভিন্নতা পরিমাপ করে। এটি রক্তাল্পতার কারণ নির্ণয়ে সহায়ক হতে পারে।",
                        "result_explanation": "RDW-SD এর জন্য কোনো নির্দিষ্ট রেফারেন্স রেঞ্জ রিপোর্টে দেওয়া হয়নি, তাই এর অবস্থা নির্ধারণ করা সম্ভব নয়। একজন ডাক্তারের পরামর্শ নিন।"
                    },
                    {
                        "test_name": "Eosinophil",
                        "value": 5.0,
                        "unit": "%",
                        "reference_range": "01-06%",
                        "status": "Normal",
                        "keyword_explanation": "ইওসিনোফিল হলো এক ধরনের শ্বেত রক্তকণিকা যা অ্যালার্জি প্রতিক্রিয়া এবং পরজীবী সংক্রমণের বিরুদ্ধে লড়াই করে।",
                        "result_explanation": "আপনার ইওসিনোফিলের শতাংশ স্বাভাবিক সীমার মধ্যে রয়েছে।"
                    }
                ],
                "risk_level": "Medium",
                "advice": "আপনার ESR এর উচ্চ মান এবং রেডিওলজি রিপোর্টে প্রাপ্ত ফুসফুসের অস্বাভাবিকতাগুলি (ডান দিকের ফুসফুসের গোড়ায় প্লুরাল রিঅ্যাকশন এবং ছোট অস্বচ্ছতা) একজন ডাক্তারের দ্বারা বিস্তারিত মূল্যায়নের প্রয়োজন। এই ফলাফলগুলির কারণ নির্ণয় এবং উপযুক্ত চিকিৎসার জন্য অবিলম্বে একজন চিকিৎসকের সাথে পরামর্শ করুন। কোনো চিকিৎসা সংক্রান্ত সিদ্ধান্ত নেওয়ার আগে সর্বদা একজন যোগ্য স্বাস্থ্যসেবা প্রদানকারীর সাথে কথা বলুন।"
            },
            {
                "summary": "এই রিপোর্টে গ্রান্থনা রহমানের ফসফেট পরীক্ষার ফলাফল বিশ্লেষণ করা হয়েছে। তার বয়স ২৪ বছর এবং ফসফেটের মাত্রা স্বাভাবিক সীমার মধ্যে পাওয়া গেছে।",
                "voice_explanation": "এই রিপোর্টে গ্রান্থনা রহমানের ফসফেট পরীক্ষার ফলাফল বিশ্লেষণ করা হয়েছে। তার বয়স ২৪ বছর এবং ফসফেটের মাত্রা ৩.৫ মিলিগ্রাম/ডেসিলিটার পাওয়া গেছে। প্রাপ্তবয়স্কদের জন্য স্বাভাবিক পরিসর হলো ২.৬ থেকে ৪.৫ মিলিগ্রাম/ডেসিলিটার। এই ফলাফল অনুযায়ী, তার ফসফেটের মাত্রা স্বাভাবিক সীমার মধ্যে রয়েছে। এটি একটি ভালো খবর এবং নির্দেশ করে যে তার শরীরে ফসফেটের ভারসাম্য ঠিক আছে।",
                "tests_analysis": [
                    {
                        "test_name": "Phosphate (Inorganic)",
                        "value": 3.5,
                        "unit": "mg/dl",
                        "reference_range": "2.6-4.5 mg/dl (Adult)",
                        "status": "Normal",
                        "keyword_explanation": "ফসফেট একটি গুরুত্বপূর্ণ খনিজ যা হাড়, দাঁত এবং শরীরের শক্তি উৎপাদনে সাহায্য করে। এটি কিডনি এবং অন্যান্য শারীরিক কার্যকারিতার জন্যও অপরিহার্য।",
                        "result_explanation": "আপনার ফসফেটের মাত্রা স্বাভাবিক সীমার মধ্যে রয়েছে, যা নির্দেশ করে যে আপনার শরীরে ফসফেটের ভারসাম্য ঠিক আছে এবং আপনার হাড় ও অন্যান্য শারীরিক কার্যকারিতা সঠিকভাবে চলছে।"
                    }
                ],
                "risk_level": "Low",
                "advice": "আপনার বর্তমান ফলাফল স্বাভাবিক। সুষম খাদ্য গ্রহণ এবং স্বাস্থ্যকর জীবনযাপন চালিয়ে যান। নিয়মিত স্বাস্থ্য পরীক্ষা করানো গুরুত্বপূর্ণ। কোনো উদ্বেগ থাকলে একজন ডাক্তারের পরামর্শ নিন।"
            }
        ],
        "IMAGING": [
            {
                "summary": "এই এক্স-রে রিপোর্টে রোগীর ডায়াফ্রাম, হৃদপিণ্ডের আকার, শ্বাসনালী এবং বুকের খাঁচার হাড় স্বাভাবিক দেখা গেছে। তবে, ডান ফুসফুসের নিচের অংশে ছোট, ঘন অস্বচ্ছতা এবং ডান সিপি অ্যাঙ্গেল আবৃত থাকার বিষয়টি লক্ষ্য করা গেছে। সামগ্রিকভাবে, এটি ডান দিকের প্লুরাল রিঅ্যাকশনের সাথে সামঞ্জস্যপূর্ণ।",
                "voice_explanation": "আপনার বুকের এক্স-রে রিপোর্টে কিছু গুরুত্বপূর্ণ তথ্য পাওয়া গেছে। ডায়াফ্রাম, হৃদপিণ্ডের আকার, শ্বাসনালী এবং বুকের খাঁচার হাড় স্বাভাবিক দেখা যাচ্ছে। তবে, ডান ফুসফুসের নিচের অংশে কিছু অস্বচ্ছতা এবং ডান সিপি অ্যাঙ্গেল আবৃত থাকার বিষয়টি লক্ষ্য করা হয়েছে। এই ফলাফলটি ডান দিকের প্লুরাল রিঅ্যাকশনের ইঙ্গিত দিচ্ছে। এটি একটি অস্বাভাবিক অবস্থা যা একজন ডাক্তারের দ্বারা মূল্যায়ন করা প্রয়োজন।",
                "tests_analysis": [
                    {
                        "test_name": "ডায়াফ্রামের অবস্থান ও আকৃতি",
                        "value": "Normal",
                        "unit": "",
                        "reference_range": "",
                        "status": "Normal",
                        "keyword_explanation": "ডায়াফ্রাম হলো ফুসফুসের নিচে অবস্থিত একটি পেশী যা শ্বাস-প্রশ্বাসে সাহায্য করে। এর অবস্থান এবং আকৃতি গুরুত্বপূর্ণ।",
                        "result_explanation": "রোগীর ডায়াফ্রামের অবস্থান এবং আকৃতি স্বাভাবিক দেখা যাচ্ছে।"
                    },
                    {
                        "test_name": "হৃদপিণ্ডের আকার (প্রস্থচ্ছেদ)",
                        "value": "Normal",
                        "unit": "",
                        "reference_range": "",
                        "status": "Normal",
                        "keyword_explanation": "বুকের এক্স-রেতে হৃদপিণ্ডের প্রস্থচ্ছেদ পরিমাপ করে এর আকার স্বাভাবিক আছে কিনা তা দেখা হয়।",
                        "result_explanation": "রোগীর হৃদপিণ্ডের প্রস্থচ্ছেদ স্বাভাবিক সীমার মধ্যে রয়েছে।"
                    },
                    {
                        "test_name": "ফুসফুস (ডান ফুসফুসের নিচের অংশে অস্বচ্ছতা)",
                        "value": "Small dense homogenous opacities are noted in right lower zone with curvilinear upper border causing obliteration of right CP angle",
                        "unit": "",
                        "reference_range": "",
                        "status": "High",
                        "keyword_explanation": "ফুসফুসে অস্বচ্ছতা বা অপাসিটি দেখা গেলে তা সংক্রমণ, প্রদাহ বা অন্য কোনো সমস্যার ইঙ্গিত দিতে পারে।",
                        "result_explanation": "রোগীর ডান ফুসফুসের নিচের অংশে ছোট, ঘন এবং সমজাতীয় অস্বচ্ছতা দেখা গেছে, যা ডান সিপি অ্যাঙ্গেলকে আবৃত করে রেখেছে। এটি একটি অস্বাভাবিক ফলাফল।"
                    },
                    {
                        "test_name": "শ্বাসনালীর অবস্থান",
                        "value": "Central",
                        "unit": "",
                        "reference_range": "",
                        "status": "Normal",
                        "keyword_explanation": "শ্বাসনালী (ট্র্যাকিয়া) হলো একটি নল যা বাতাসকে ফুসফুসে নিয়ে যায়। এর কেন্দ্রীয় অবস্থান স্বাভাবিক।",
                        "result_explanation": "রোগীর শ্বাসনালী স্বাভাবিকভাবে কেন্দ্রীয় অবস্থানে রয়েছে।"
                    },
                    {
                        "test_name": "বুকের খাঁচার হাড়",
                        "value": "No abnormality",
                        "unit": "",
                        "reference_range": "",
                        "status": "Normal",
                        "keyword_explanation": "বুকের খাঁচার হাড়ের গঠন পরীক্ষা করা হয় কোনো অস্বাভাবিকতা বা আঘাত আছে কিনা তা দেখতে।",
                        "result_explanation": "রোগীর বুকের খাঁচার হাড়ে কোনো অস্বাভাবিকতা দেখা যায়নি।"
                    },
                    {
                        "test_name": "সামগ্রিক ধারণা (ইম্প্রেশন)",
                        "value": "Consistent with Right basal Pleural Reaction",
                        "unit": "",
                        "reference_range": "",
                        "status": "High",
                        "keyword_explanation": "প্লুরাল রিঅ্যাকশন বলতে ফুসফুসের বাইরের আবরণে (প্লুরা) প্রদাহ বা তরল জমার প্রতিক্রিয়া বোঝায়।",
                        "result_explanation": "এক্স-রে রিপোর্ট অনুযায়ী, রোগীর ডান ফুসফুসের নিচের অংশে প্লুরাল রিঅ্যাকশনের সাথে সামঞ্জস্যপূর্ণ ফলাফল পাওয়া গেছে।"
                    }
                ],
                "risk_level": "Medium",
                "advice": "এই রিপোর্টটি একজন যোগ্যতাসম্পন্ন ডাক্তারের সাথে আলোচনা করা অত্যন্ত গুরুত্বপূর্ণ। ডাক্তার আপনার ক্লিনিক্যাল লক্ষণ এবং অন্যান্য ল্যাবরেটরি পরীক্ষার ফলাফলের সাথে এই এক্স-রে রিপোর্টটি মিলিয়ে দেখবেন এবং প্রয়োজনীয় পরবর্তী পদক্ষেপ বা চিকিৎসার পরামর্শ দেবেন। নিজে নিজে কোনো সিদ্ধান্ত নেবেন না।"
            }
        ]
    },
    "summary": {
        "total_tests": 18,
        "abnormal_count": 3,
        "critical_count": 0,
        "has_critical": false
    },
    "is_multi_patient": false
},

  // 2. For multiple patient report
  MULTI_PATIENT: {
    "is_multi_patient": true,
    "total_patients": 2,
    "patients": [
      {
        "is_mixed": false,
        "document_type": { "category": "CLINICAL", "sub_type": "PROGRESS", "confidence": "HIGH", "is_mixed": false },
        "patient": { "name": "John Doe", "age_years": null, "gender": "male", "report_type": "PROGRESS" },
        "report": {
          "summary": "Patient reports persistent lower back pain for 3 weeks.",
          "voice_explanation": "John is experiencing sharp lower back pain radiating to his left leg. The diagnosis is a lumbar strain.",
          "tests_analysis": [
            { "test_name": "Finding 1", "result_explanation": "Chief Complaint: Persistent lower back pain." },
            { "test_name": "Finding 6", "result_explanation": "Primary Diagnosis: Lumbar Strain (ICD-10: M54.50)." }
          ],
          "risk_level": "Unknown",
          "advice": "Physical Therapy (2x weekly for 4 weeks)."
        },
        "sections": {},
        "summary": { "total_tests": 8, "abnormal_count": 0, "critical_count": 0, "has_critical": false },
        "patient_index": 0
      },
      {
        "is_mixed": false,
        "document_type": { "category": "CLINICAL", "sub_type": "PROGRESS", "confidence": "HIGH", "is_mixed": false },
        "patient": { "name": "GR Rahman", "age_years": 24, "gender": "female", "report_type": "PROGRESS" },
        "report": {
          "summary": "Similar clinical presentation as previous case with slight variations in vitals.",
          "voice_explanation": "This patient also has lumbar strain symptoms. Vitals are stable but pain is significant.",
          "tests_analysis": [
            { "test_name": "Finding 4", "result_explanation": "Vital Signs: BP: 125/80 mmHg | HR: 72 bpm" }
          ],
          "risk_level": "Unknown",
          "advice": "Follow-up in 14 days."
        },
        "sections": {},
        "summary": { "total_tests": 8, "abnormal_count": 0, "critical_count": 0, "has_critical": false },
        "patient_index": 1
      }
    ]
  },

  // 3. Single report proper data demo
  SINGLE_REPORT_PROPER: {
    "is_mixed": false,
    "document_type": {
      "category": "LAB",
      "sub_type": "CBC",
      "confidence": "HIGH",
      "is_mixed": false
    },
    "patient": {
      "name": "GRANTHANA RAHMAN",
      "age_years": 24,
      "gender": "female",
      "collection_date": "2024-11-05",
      "referred_by": "DR.MD.AZIZUL KAHHAR",
      "lab_no": "22411208208",
      "invoice_no": "D2411127699"
    },
    "report": {
      "summary": "This report shows that most of your blood test results are within the normal range. However, your ESR is elevated.",
      "voice_explanation": "Hello. Your blood test results are mostly normal, which is good news. Your red blood cells, white blood cells, and platelets are all within healthy ranges. The only finding that stands out is your ESR, or Erythrocyte Sedimentation Rate, which is a bit high. This can sometimes indicate inflammation or infection in the body.",
      "tests_analysis": [
        {
          "test_name": "Total Count (WBC)",
          "value": 10.74,
          "unit": "X10^9/L",
          "reference_range": "4.00-11.00X10^9/L",
          "status": "Normal",
          "keyword_explanation": "White Blood Cells fight infections.",
          "result_explanation": "Your White Blood Cell count is normal."
        },
        {
          "test_name": "ESR (Erythrocyte Sedimentation Rate)",
          "value": 47.0,
          "unit": "mm in 1st hr.",
          "reference_range": "0-20 mm in 1st hr.",
          "status": "High",
          "keyword_explanation": "ESR is a marker for inflammation.",
          "result_explanation": "Your ESR is 47 mm, which is higher than normal."
        }
      ],
      "risk_level": "Medium",
      "advice": "Consult with your doctor regarding the elevated ESR.",
      "raw_text": "HAEMATOLOGYREPORT..."
    },
    "summary": {
      "total_tests": 16,
      "abnormal_count": 1,
      "critical_count": 0,
      "has_critical": false
    }
  }
};
