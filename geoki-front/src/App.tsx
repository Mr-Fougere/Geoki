import { useEffect, useState } from "react";
import "./App.css";
import SelectDepartment from "./SelectDepartment";
import SynchroPage from "./SynchroPage";
import SocketIOService from "./SocketIOService";
import { Socket } from "socket.io-client";
import ChatPage from "./ChatPage";

enum State {
  Initial = "initialState",
  Synchro = "synchroState",
  Starting = "startingState",
  Running = "runningState",
  Finish = "finishState",
}

type Department = {
  name: string;
  code: string;
};


function App() {

  const socketService = new SocketIOService("http://127.0.0.1:5000");

  const [state, setState] = useState(State.Running);
  const [department, setDepartment] = useState<Department>();
  const [contentPage, setContentPage] = useState<any>();
  const [socket, setSocket] = useState<Socket>(socketService.connect());

  const updateContentPage = (): any => {
    switch (state) {
      case State.Synchro:
        setContentPage(<SynchroPage ></SynchroPage>);
        break;
      case State.Running:
        setContentPage(<ChatPage></ChatPage>)
        break;
      default:
        setContentPage(<SelectDepartment socket={socket} setDepartment={setDepartment} />);
        break;
    }
  };

  useEffect(() => {
    updateContentPage()
  }, [state]);
  
  return (
    <>
      <div>
        <img src="logo.png" alt="logo" className="logo" />
        {contentPage}
      </div>
    </>
  );
}

export default App;
