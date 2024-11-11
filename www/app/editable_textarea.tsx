import { useState, useRef, ChangeEvent, useEffect } from "react";

export default function EditableTextArea({ item, onChange }:{ item:{role:string, content:string, name:string }, onChange:(value:string) => void}) {
    const [dirty, setDirty] = useState("");
	const timeoutID = useRef<NodeJS.Timeout>();

    useEffect(() => {
        if(dirty == item.content) {
            setDirty("");
        }
    }, [dirty, item.content])

	function changeMessage(message:string) {
        setDirty(message);
		clearTimeout(timeoutID.current);
		timeoutID.current = setTimeout(() => {
			onChange(message);
		}, 1000)
	}

    return (
        <div className="relative">
            <label className="whitespace-pre-wrap">{dirty?dirty:item.content}</label>
            <textarea
                value={dirty?dirty:item.content}
                onChange={(event:ChangeEvent<HTMLTextAreaElement>) => {
                    changeMessage(event.target.value);
                }}
                className="w-full h-full absolute top-0 left-0 resize-none overflow-hidden bg-transparent outline-0"
            ></textarea>
        </div>
    );
}