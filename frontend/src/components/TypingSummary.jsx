import { useState, useEffect, useRef } from "react";

export default function TypingSummary({ summary }) {
    const [displayText, setDisplayText] = useState([]);

  const speechQueueRef = useRef([]);
  const speakingRef = useRef(false);
  const hasStartedRef = useRef(false);     // prevents StrictMode double run
  const lastSpokenRef = useRef("");        // prevents duplicate speech

  /* ===========================
     SPEAK FUNCTION
  ============================ */
  const speakText = (text) => {
    if (!text) return;

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "en-US";
    utterance.rate = 1;
    utterance.pitch = 1;

    utterance.onend = () => {
      speakingRef.current = false;

      if (speechQueueRef.current.length > 0) {
        const nextText = speechQueueRef.current.shift();
        speakText(nextText);
      }
    };

    speakingRef.current = true;
    window.speechSynthesis.speak(utterance);
  };

  /* ===========================
     QUEUE FUNCTION (SAFE)
  ============================ */
  const queueSpeech = (text) => {
    if (!text) return;

    // Prevent duplicate speech
    if (text === lastSpokenRef.current) return;
    lastSpokenRef.current = text;

    if (speakingRef.current) {
      speechQueueRef.current.push(text);
    } else {
      speakText(text);
    }
  };

  /* ===========================
     RESET WHEN SUMMARY CHANGES
  ============================ */
  useEffect(() => {
    hasStartedRef.current = false;
  }, [summary]);

  /* ===========================
     MAIN TYPING + SPEECH EFFECT
  ============================ */
  useEffect(() => {
    if (!summary || !Array.isArray(summary)) return;

    // Prevent StrictMode double execution
    if (hasStartedRef.current) return;
    hasStartedRef.current = true;

    // Clear previous speech
    window.speechSynthesis.cancel();
    speechQueueRef.current = [];
    speakingRef.current = false;
    lastSpokenRef.current = "";

    let tempDisplay = [];
    let currentIndex = 0;

    function typeNext() {
      if (currentIndex >= summary.length) return;

      const currentItem = summary[currentIndex];

      tempDisplay.push({ title: "", description: "", keyword: "", result: "" });
      setDisplayText([...tempDisplay]);

      let charIndexTitle = 0;

      function typeTitle() {
        if (charIndexTitle < currentItem.title.length) {
          tempDisplay[tempDisplay.length - 1].title +=
            currentItem.title[charIndexTitle];

          setDisplayText([...tempDisplay]);
          charIndexTitle++;
          setTimeout(typeTitle, 30);
        } else {
          // Speak title once fully typed
          queueSpeech(currentItem.title);

          // Handle test array
          if (Array.isArray(currentItem.description)) {
            let tests_analysis = currentItem.description;
            let testIndex = 0;

            function typeTest() {
              if (testIndex >= tests_analysis.length) {
                currentIndex++;
                typeNext();
                return;
              }

              const test = tests_analysis[testIndex];

              tempDisplay[tempDisplay.length - 1] = {
                title: "",
                keyword: "",
                result: "",
                status: "",
                unit:"",
                reference_range : "",
                value: ""
              };
              setDisplayText([...tempDisplay]);

              let charIndexTestTitle = 0;
              let charIndexKeyword = 0;
              let charIndexResult = 0;

              function typeTestTitle() {
                if (charIndexTestTitle < test.test_name.length) {
                  tempDisplay[tempDisplay.length - 1].title +=
                    test.test_name[charIndexTestTitle];

                  setDisplayText([...tempDisplay]);
                  charIndexTestTitle++;
                  setTimeout(typeTestTitle, 30);
                } else {
                  //queueSpeech(test.test_name);
                  typeKeyword();
                }
              }

              function typeKeyword() {
                if (charIndexKeyword < test.keyword_explanation.length) {
                  tempDisplay[tempDisplay.length - 1].keyword +=
                    test.keyword_explanation[charIndexKeyword];

                  setDisplayText([...tempDisplay]);
                  charIndexKeyword++;
                  setTimeout(typeKeyword, 20);
                } else {
                  // queueSpeech(
                  //   `Keyword Explanation: ${test.keyword_explanation}`
                  // );
                  typeResult();
                }
              }

              function typeResult() {
                if (charIndexResult < test.result_explanation.length) {
                  tempDisplay[tempDisplay.length - 1].result +=
                    test.result_explanation[charIndexResult];

                  setDisplayText([...tempDisplay]);
                  charIndexResult++;
                  setTimeout(typeResult, 20);
                } else {
                  // queueSpeech(
                  //   `Result Explanation: ${test.result_explanation}`
                  // );
                  tempDisplay[tempDisplay.length - 1].status          = test.status;
                  tempDisplay[tempDisplay.length - 1].unit            = test.unit;
                  tempDisplay[tempDisplay.length - 1].reference_range = test.reference_range;
                  tempDisplay[tempDisplay.length - 1].value           = test.value;

                  testIndex++;
                  tempDisplay.push({
                    title: "",
                    keyword: "",
                    result: "",
                    status: "",
                    unit:"",
                    reference_range : "",
                    value: ""
                  });

                  typeTest();
                }
              }

              typeTestTitle();
            }

            typeTest();
          }
          // Handle normal description
          else if (typeof currentItem.description === "string") {
            let charIndexDesc = 0;
            let wordCount = 0;
            let currentWord = "";
            let speechChunk = "";

            function typeDesc() {
              if (charIndexDesc < currentItem.description.length) {
                const currentChar = currentItem.description[charIndexDesc];
                tempDisplay[tempDisplay.length - 1].description += currentChar;

                if (currentChar !== " " && currentChar !== "\n" && currentChar !== ",") {
                  currentWord += currentChar;
                } else {
                  // Word completed
                  if (currentWord.trim().length > 0) {
                    wordCount++;
                    speechChunk += currentWord + " ";
                    currentWord = "";

                    // 🔥 Speak after 10 words
                    if (wordCount > 10 && currentChar === ",") {
                      queueSpeech(speechChunk);
                      speechChunk = "";
                      wordCount = 0;
                    }
                  }
                }
                setDisplayText([...tempDisplay]);
                charIndexDesc++;
                setTimeout(typeDesc, 30);
              } else {
                // Speak full description once completed
                if (currentWord.trim() !== "") {
                  queueSpeech(speechChunk + " " + currentWord );
                  speechChunk = "";
                }
                currentIndex++;
                typeNext();
              }
            }

            typeDesc();
          } else {
            currentIndex++;
            typeNext();
          }
        }
      }

      typeTitle();
    }

    typeNext();

    return () => {
      window.speechSynthesis.cancel();
      speechQueueRef.current = [];
      speakingRef.current = false;
      lastSpokenRef.current = "";
    };
  }, [summary]);

  return (
    <div style={{ maxWidth: "800px", margin: "0 auto", textAlign:"start"}}>
      {displayText.map((item, idx) => (
        <div
          key={idx}
          style={{
            textAlign:"start"
          }}
        >
          {item.title && <h3 style={{ color: "#4f46e5", marginBottom: "10px" }}>{item.title}</h3>}

          {item.description && <p>{item.description}</p>}

          {item.keyword && (
            <>
              <p>
                <strong>Keyword Explanation: </strong>
                {item.keyword}
              </p>
              {item.result && (
                <p>
                  <strong>Result Explanation: </strong>
                  {item.result}
                </p>
              )}
              {item.value && <p style={{ color: item.status === "Low" ? "orange" : item.status === "High" ? "red" : "green" }}>
                {item.title}: {item.value} {item.unit} {item.status}
              </p>}
            </>
          )}
          
        </div>
      ))}
    </div>
  );
}