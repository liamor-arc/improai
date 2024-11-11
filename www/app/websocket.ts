"use client"

export default class WebSocketConnection {
    host:string;
    port:number;
    connection:WebSocket|null;

    constructor(host:string, port:number) {
        this.host = host;
        this.port = port;
        this.connection = null;
    }

    isConnecting() {
        return this.connection != null && this.connection.readyState === WebSocket.CONNECTING;
    }

    isOpen() {
        return this.connection != null && this.connection.readyState === WebSocket.OPEN;
    }

    isConnected() {
        return this.connection != null && this.connection.readyState !== WebSocket.CLOSING && this.connection.readyState !== WebSocket.CLOSED;
    }

    connect() {
        if(this.connection != null) {
            this.connection.close();
        }
        this.connection = new WebSocket(`ws://${this.host}:${this.port}`);
    }

    close() {
        this.connection?.close();
    }
}