import React, { useState, useEffect } from 'react';
import './App.css';
import courseData from './comp_eng_courses.json';
import { GoogleGenerativeAI } from '@google/generative-ai';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');

  const geminiApiKey = process.env.REACT_APP_GEMINI_API_KEY;
  const genAI = new GoogleGenerativeAI(geminiApiKey);
  const model = genAI.getGenerativeModel({ model: "gemini-2.0-flash-001" });

  useEffect(() => {
    if (!geminiApiKey) {
      alert("Please set the REACT_APP_GEMINI_API_KEY environment variable.");
    }
  }, [geminiApiKey]);

  const sendMessage = async (event) => {
    event.preventDefault();
    if (!geminiApiKey) {
      alert("Please set the REACT_APP_GEMINI_API_KEY environment variable.");
      return;
    }

    setMessages([...messages, { text: input, sender: 'user' }]);

    // try {
    //   const response = await fetch('https://www.northwestern.edu/course-data.json'); // Replace with actual URL
    //   const data = await response.json();

      const prompt = `I ONLY WANT YOU TO RETURN CLASSES AND THE JUSTIFICATION (2-3 sentences per class), DO NOT START YAPPING.Based on the following course data from Northwestern University, and the user's message: ${input}, recommend a few courses and justify your recommendations based on the users input career dreams, make it so that your reccomendations work towards the users degree and are things that can actually be applied as credits to graduate (i.e don't reccomend two classes that fill the same graduation requirement) also make it so that you don't reccomend courses they've indicated they already took-> and make sure all prerequisites are met and if they aren't met reccomend that the user takes those prerequisite classes first:\n${JSON.stringify(courseData)}`;

      const result = await model.generateContent(prompt);
      const responseText = result.response.text();

      // Extract course recommendations and justifications
      const courseRegex = /([A-Z_]+\s*\d+[^:]*?)(\n{2,}(.*?))(?=\n|$)/g;
      let match;
      const courses = [];

      while ((match = courseRegex.exec(responseText)) !== null) {
        const courseName = match[1].trim();
        const justification = match[3].trim();

        courses.push({
          courseName: courseName.trim(),
          justification: justification.trim()
        });
      }

      if (courses.length === 0) {
        console.error("Failed to parse courses from responseText:", responseText);
      }

      // Format the extracted courses into JSON
      const formattedResponse = JSON.stringify({ courses }, null, 2);

      setMessages([...messages, { text: input, sender: 'user' }, { text: formattedResponse, sender: 'bot' }]);
    // } catch (error) {
    //   console.error("Error generating content:", error);
    //   setMessages([...messages, { text: input, sender: 'user' }, { text: "Error generating response. Please try again." + error, sender: 'bot' }]);

    setInput('');
  };

  return (
    <div className="flex flex-col h-screen bg-gray-100">
      <div className="bg-white py-4 shadow-md">
        <h1 className="text-2xl font-bold text-center">Northwestern University I love You </h1>
      </div>
      <div className="flex-grow overflow-y-auto p-4">
        {messages.map((message, index) => (
          <div
            key={index}
            className={`mb-2 p-2 rounded-lg ${
              message.sender === 'user' ? 'bg-blue-200 ml-auto' : 'bg-gray-200 mr-auto'
            }`}
          >
            {message.text}
          </div>
        ))}
      </div>
      <form className="p-4 flex items-center" onSubmit={sendMessage}>
        <input
          className="flex-grow rounded-l-md py-2 px-4 border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
          type="text"
          placeholder="Type your message..."
          value={input}
          onChange={(event) => setInput(event.target.value)}
        />
        <button
          className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-r-md focus:outline-none focus:shadow-outline"
          type="submit"
        >
          Send
        </button>
      </form>
    </div>
  );
}

export default App;