"use client";

import WebSocketConnection from "./websocket";
import Image from "next/image";
import { ChangeEvent, Fragment, useEffect, useRef, useState } from "react";
import EditableTextArea from "./editable_textarea";

export default function Home() {
	const [conversation, setConversation] = useState<{role:string,name:string,content:string}[]>([]);
	const [showInstructions, setShowInstructions] = useState(false);
	const [instructions, setInstructions] = useState("");
	const [transcribing, setTranscribing] = useState(false);
	const [generating, setGenerating] = useState(false);
	const [dirtyInstructions, setDirtyInstructions] = useState("");
	const [name, setName] = useState("");
	const [prompt, setPrompt] = useState("");
	const [scroll, setScroll] = useState(true);
	const [scrollTop, setScrollTop] = useState(0);
	const socket = useRef(new WebSocketConnection("127.0.0.1", 4000));
	const scrollElement = useRef<HTMLDivElement>(null);

	useEffect(() => {
		function onOpen() {
			console.log("open");
			socket.current.connection?.send(JSON.stringify({
				action: "conversation"
			}));
		}

		function onMessage(event:MessageEvent) {
			console.log(event)
			const data = JSON.parse(event.data);
			if(data.action == "conversation") {
				setConversation(data.conversation);
				setInstructions(data.conversation[0].content);
				setTranscribing(data.transcribing);
				setGenerating(data.generating);
			}
		}

		function onScroll() {
			setScroll(false);
			if(scrollElement.current) {
				setScrollTop(scrollElement.current.scrollTop);
			}
		}

		scrollElement.current?.addEventListener("scroll", onScroll);

		if(!socket.current.isConnected()) {
			socket.current.connect();
			socket.current.connection?.addEventListener("message", onMessage);
		}
		if(socket.current.isConnecting()) {
			socket.current.connection?.addEventListener("open", onOpen);
			return () => {
				socket.current.connection?.removeEventListener("open", onOpen);
				socket.current.close();
			}
		} else {
			onOpen();
			return () => {
				socket.current.close();
			}
		}
	}, []);

	useEffect(() => {
		if(scroll) {
			scrollElement.current?.scrollTo({ top: scrollElement.current.scrollHeight });
		}
	}, [scroll, conversation])

	useEffect(() => {
		if(scrollElement.current && scrollTop + scrollElement.current?.clientHeight >= scrollElement.current?.scrollHeight) {
			console.log("scroll true");
			setScroll(true);
		}
	}, [scrollTop])

	function resumeScrolling() {
		setScroll(true);
	}

	function openInstructions() {
		setShowInstructions(true);
	}

	function closeInstructions() {
		setShowInstructions(false);
	}

	function cancelInstructions() {
		setDirtyInstructions("");
		setShowInstructions(false);
	}

	function submitInstructions() {
		if (dirtyInstructions) {
			setDirtyInstructions("");
			setInstructions(dirtyInstructions);
			socket.current.connection?.send(JSON.stringify({
				action: "instructions",
				instructions: dirtyInstructions
			}))
		}
		closeInstructions();
	}

	function changeInstructions(event:ChangeEvent<HTMLTextAreaElement>) {
		setDirtyInstructions(event.target.value);
	}

	function changeEditMessage(index:number, message:string) {
		socket.current.connection?.send(JSON.stringify({
			action: "change",
			index: index,
			message: message 
		}));
	}

	function removeMessage(index:number) {
		socket.current.connection?.send(JSON.stringify({
			action: "remove",
			index: index
		}));
	}

	function toggleTranscribing() {
		let command = "Start Transcribing";
		if(transcribing) {
			command = "Stop Transcribing";
		} 
		socket.current.connection?.send(JSON.stringify({
			action: "command",
			command: command
		}));
		setTranscribing(!transcribing);
	}

	function changeName(event:ChangeEvent<HTMLInputElement>) {
		setName(event.target.value);
	}

	function changePrompt(event:ChangeEvent<HTMLInputElement>) {
		setPrompt(event.target.value);
	}

	function submitPrompt() {
		if(prompt.length === 0) {
			socket.current.connection?.send(JSON.stringify({
				action: "assistant"
			}));
		} else {
			socket.current.connection?.send(JSON.stringify({
				action: "append",
				name: name,
				message: prompt,
				generate: true
			}));
		}
		setName("");
		setPrompt("");
	}

	function playMessage(index:number) {
		socket.current.connection?.send(JSON.stringify({
			action: "play",
			message: conversation[index].content
		}));
	}

	return (
		<Fragment>
			<div className={(showInstructions?"":"hidden ") + "relative z-10"}>
				<div className="fixed inset-0 bg-gray-300 bg-opacity-75 transition-opacity"></div>
				<div className="fixed inset-0 z-10 w-screen overflow-y-auto">
					<div className="flex h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
					<div className="flex flex-col relative transform overflow-hidden rounded-lg bg-white text-left shadow-xl transition-all sm:my-8 sm:w-2/3 h-2/3">
						<div className="flex-1 bg-white px-4 pb-4 pt-5 sm:p-6 sm:pb-4">
							<div className="relative w-full h-full min-w-[200px]">
								<textarea value={dirtyInstructions?dirtyInstructions:instructions} onChange={changeInstructions} className="peer h-full min-h-[100px] w-full resize-none rounded-[7px] border border-blue-gray-200 bg-transparent px-3 py-2.5 font-sans text-sm font-normal text-blue-gray-700 outline outline-0 transition-all placeholder-shown:border placeholder-shown:border-blue-gray-200 placeholder-shown:border-t-blue-gray-200 focus:border-2 focus:border-gray-900 focus:border-t-transparent focus:outline-0 disabled:resize-none disabled:border-0 disabled:bg-blue-gray-50" placeholder=" "/>
								<label className="before:content[' '] after:content[' '] pointer-events-none absolute left-0 -top-1.5 flex h-full w-full select-none text-[11px] font-normal leading-tight text-blue-gray-400 transition-all before:pointer-events-none before:mt-[6.5px] before:mr-1 before:box-border before:block before:h-1.5 before:w-2.5 before:rounded-tl-md before:border-t before:border-l before:border-blue-gray-200 before:transition-all after:pointer-events-none after:mt-[6.5px] after:ml-1 after:box-border after:block after:h-1.5 after:w-2.5 after:flex-grow after:rounded-tr-md after:border-t after:border-r after:border-blue-gray-200 after:transition-all peer-placeholder-shown:text-sm peer-placeholder-shown:leading-[3.75] peer-placeholder-shown:text-blue-gray-500 peer-placeholder-shown:before:border-transparent peer-placeholder-shown:after:border-transparent peer-focus:text-[11px] peer-focus:leading-tight peer-focus:text-gray-900 peer-focus:before:border-t-2 peer-focus:before:border-l-2 peer-focus:before:border-gray-900 peer-focus:after:border-t-2 peer-focus:after:border-r-2 peer-focus:after:border-gray-900 peer-disabled:text-transparent peer-disabled:before:border-transparent peer-disabled:after:border-transparent peer-disabled:peer-placeholder-shown:text-blue-gray-500">
									Instructions
								</label>
							</div>
						</div>
						<div className="bg-gray-50 px-4 py-3 sm:flex sm:flex-row-reverse sm:px-6">
							<button onClick={submitInstructions} type="button" className="inline-flex w-full justify-center rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 sm:ml-3 sm:w-auto">Save</button>
							<button onClick={cancelInstructions} type="button" className="mt-3 inline-flex w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:mt-0 sm:w-auto">Cancel</button>
						</div>
					</div>
					</div>
				</div>
			</div>
			<div className="flex h-screen antialiased text-gray-800">
				<div className="flex flex-col flex-auto h-full p-6">
					<div ref={scrollElement} className="flex flex-col h-full overflow-x-auto mb-4 px-10">
						{
							conversation.map((item, index) => {
								return (
								<div key={index} className={(item.role=="assistant"?"justify-end ":"") + "flex m-1"}>
									<div className={(item.role=="assistant"?"bg-green-500 text-white ":"bg-gray-300 ") + "flex py-1 px-3 max-w-[90%] gap-3 rounded-lg overflow-hidden"}>
										<div className="min-w-20 content-center">{index==0?("Instructions"):item.name}</div>
										{index!==0?(
											<EditableTextArea item={item} onChange={(value:string) => changeEditMessage(index, value)}/>
										):(<div className="text-gray-700">{item.content}</div>)}
									</div>
									{index!=0?(
										<div className="content-center pl-2">
											<Image onClick={() => removeMessage(index)} src="/rubbish-bin.png" alt="Remove Message" width={15} height={15} className="mr-1 cursor-pointer inline-block"/>
											<Image onClick={() => playMessage(index)} src="/speaker-filled-audio-tool.png" alt="Play Audio" width={15} height={15} className="cursor-pointer inline-block"/>
										</div>
									):""}
								</div>);
							})
						}
						<div key="generating" className={(generating?"":"hidden ") + "justify-end flex m-1"}>
							<div className="py-1 px-3 max-w-[90%] gap-3 rounded-lg">
								Generating ...
							</div>
						</div>
					</div>
					<div className="relative flex flex-row items-center h-16 rounded-xl bg-white w-full px-4">
						<div className={(scroll?"hidden ":"") + "absolute left-0 top-[-30px] items-center justify-center w-full"}>
							<div onClick={resumeScrolling} className="w-64 mx-auto text-center cursor-pointer bg-blue-500 rounded-full text-white">
								Resume auto scroll
							</div>
						</div>
						<div className="row-start-3 flex gap-6 flex-wrap items-center justify-center w-full">
							<div className="flex items-center bg-white w-full">
								<div className="p-4">
									<Image onClick={openInstructions} src="/cog-wheel-silhouette.png" alt="Settings" width={25} height={25} className="cursor-pointer"/>
								</div>
								<div className="flex flex-row w-full rounded-l-full border-y border-l overflow-hidden">
									<input onChange={changeName} value={name} type="text" name="prompt" className="py-[13px] border-r pl-4 pr-1 text-gray-700 leading-tight w-28 focus:outline-none" placeholder="Name" />
									<input onChange={changePrompt} value={prompt} type="text" name="prompt" className="py-[13px] pr-6 pl-2 text-gray-700 leading-tight w-full focus:outline-none" placeholder="Write your prompt here..." />
								</div>
								<div>
									<button onClick={submitPrompt} type="submit" className="flex items-center bg-blue-500 justify-center w-12 h-12 text-white rounded-r-full">
										<Image src="/arrow.png" alt="Submit" width={40} height={40}/>
									</button>
								</div>
								<div>
									<div onClick={toggleTranscribing} className={(transcribing?"bg-green-500":"bg-red-500")+" m-2 w-7 h-7 rounded-full cursor-pointer"}>&nbsp;</div>
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>
		</Fragment>
	);
}
