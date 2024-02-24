class SpeechToText {
    recognition: SpeechRecognition;
    private _onresult: Function | null = null;
    private _onspeechstart: Function | null = null;
    private _onspeechend: Function | null = null;

    constructor() {
        this.recognition = new window.webkitSpeechRecognition();
        this.recognition.lang = 'fr-FR';
        this.recognition.continuous = true;
        this.recognition.interimResults = false;

        this.recognition.onstart = () => {
            console.log('Début de la reconnaissance vocale');
        };

        this.recognition.onresult = (event) => {
            if (this._onresult) {
                this._onresult(event);
            }
        };

        this.recognition.onspeechend = () => {
            if(this._onspeechend) {
                this._onspeechend();
            }
        };

        this.recognition.onspeechstart = () => {
            if(this._onspeechstart) {
                this._onspeechstart();
            }
        }

        this.recognition.onerror = (event) => {
            console.error('Erreur de reconnaissance vocale:', event.error);
        };
    }

    set onresult(callback: Function) {
        this._onresult = callback;
    }

    set onspeechstart(callback: Function) {
        this._onspeechstart = callback;
    }

    set onspeechend(callback: Function) {
        this._onspeechend = callback;
    }

    start() {
        this.recognition.start();
    }

    stop() {
        this.recognition.stop();
    }
}

export default SpeechToText;
