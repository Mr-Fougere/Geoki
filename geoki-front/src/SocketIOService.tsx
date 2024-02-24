import { io, Socket } from "socket.io-client";

class SocketIOService {
  private socket: Socket | null = null;

  constructor(private serverUrl: string) {}

  connect(): Socket {
    if (!this.socket) {
      this.socket = io(this.serverUrl);

      this.socket.on("connect", () => {
        console.log("Connecté au serveur Socket.IO");
      });

      this.socket.on("disconnect", () => {
        console.log("Déconnecté du serveur Socket.IO");
      });

      this.socket.on("error", (error: any) => {
        console.error("Erreur de connexion Socket.IO :", error);
      });
    }

    return this.socket;
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  subscribeToDepartment(callback: (data: any) => void) {
    this.socket?.on("department", callback);
  }

  subscribeToPointOfInterest(callback: (data: any) => void) {
    this.socket?.on("point_of_interest", callback);
  }
}

export default SocketIOService;
