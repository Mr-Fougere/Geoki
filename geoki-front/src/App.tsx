import { useEffect, useState } from "react";
import SpeechToText from "./services/SpeechToText";
import './App.css'

function App() {

  const [transcription, setTranscription] = useState<string>("");
  const [speaking, setSpeaking] = useState<boolean>(false);

  
  useEffect(() => {
    if ("SpeechRecognition" in window || "webkitSpeechRecognition" in window) {
      const speechRecognition = new SpeechToText()
      speechRecognition.start()
      speechRecognition.onresult = (event: SpeechRecognitionEvent) => {
        setTranscription( transcription + event.results[event.results.length - 1][0].transcript);
        setSpeaking(false);
      }
      speechRecognition.onspeechstart = () => {
        setSpeaking(true);
      }
      speechRecognition.onspeechend = () => {
        setSpeaking(false);
      }
    } else {
        console.error("SpeechRecognition API is not supported in this browser.");
    }
  }, [])
  

  return (
      <>
        <div className={`speaking-block ${speaking && "active"}`}>
          <img src="micro.png" alt="microphone" />
        </div>
        <h2>Transcription: {transcription}</h2>
      </>
  );
}

export default App;
