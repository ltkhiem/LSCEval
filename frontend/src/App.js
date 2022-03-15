import React, { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';
import './App.css';
import appConfig from './config.json'
import Button from 'react-bootstrap/Button';

const FIXED_TIME = 60;

const App = () => {
    const [query, setQuery] = useState("Waiting to start.")
    const [time, setTime] = useState(0)
    const [sessionId, setSessionId] = useState("Session ID")
    const [score, setScore] = useState(0)
    const [totalScore, setTotalScore] = useState(0)


    const handleChange = (event) => {
        setSessionId(event.target.value);
    }


    const handleFinishQuery = (event) => {
	    setTime(0)
    }


    const handleSubmit = (event) => {
        const response = axios.get(appConfig['evalserver_url'] + '?session_name=' + sessionId,
            {
                headers: { 'Content-Type': 'text/plain' }
            }
        );
        response.then((res) => {
            if (res.data.query !== "The End.") {
                setTime(FIXED_TIME);
            }
            setQuery(res.data.query);
            setScore(res.data.score);
            setTotalScore(res.data.total_score);
        });
        event.preventDefault();
    }

    useEffect(() => {
        let myInterval = setInterval(() => {
            if (time > 0) {
                setTime(time - 1);
                if (query !== "The End." && query !== "Waiting to start."){
                    const response = axios.get(appConfig['evalserver_url'] + 'get_score?session_name=' + sessionId + "&time=" + time,
                        {
                            headers: { 'Content-Type': 'text/plain' }
                        }
                    );
                    response.then((res) => {
                        setScore(res.data.score);
                        setTotalScore(res.data.total_score);
                    });
                }
            }
            if (time === 0) {
                clearInterval(myInterval);
                const response = axios.get(appConfig['evalserver_url'] + 'next_clue?session_name=' + sessionId,
                    {
                        headers: { 'Content-Type': 'text/plain' }
                    }
                );
                if (query !== "The End." && query !== "Waiting to start."){
                    response.then((res) => {
                        if (res.data.query !== "The End."){
                            setScore(res.data.score);
                            setTotalScore(res.data.total_score);
                        }
                        console.log(res.data.query);
                        setQuery(res.data.query);
                        setTime(res.data.query === "The End."? 0 :FIXED_TIME);
                    });
                }
            }
        }, 1000)
        return () => {
            clearInterval(myInterval);
        };
    }, [query, time, score]);


    return (
        <div className="App">
            <form onSubmit={handleSubmit}>
                <label>
                    Session ID
          <input type="text" value={sessionId} onChange={handleChange} />
                </label>
                <input type="submit" value="Submit" />
            </form>
            <header className="App-header">
                <pre className="text">
                    {query}
                </pre>
                <p className="text">
                    Time: {time}s
                </p>
                <p className="text">
                    Score: {score}
                </p>
                <p className="text">
                    Total: {totalScore}
                </p>
	    <Button onClick={handleFinishQuery} variant="success">Finish</Button>
            </header>
        </div>
    );
}

export default App;
