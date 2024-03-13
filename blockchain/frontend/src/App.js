import React, { useState } from 'react';
import axios from 'axios';

function App() {
    const [formData, setFormData] = useState({
        resourceType: '',
        capacity: 0,
        vCPU: 0,
        pricePerHour: 0,
    });
    const [estimatedCost, setEstimatedCost] = useState('');

    const handleChange = (e) => {
        setFormData({...formData, [e.target.name]: e.target.value });
    };

    const handleSubmit = async(e) => {
        e.preventDefault();
        try {
            const response = await axios.post('http://localhost:3000/registerResource', formData);
            setEstimatedCost(response.data.estimatedCost);
        } catch (error) {
            console.error('Error submitting form:', error);
        }
    };

    return ( <
        div className = "App" >
        <
        h1 > Register Resource < /h1> <
        form onSubmit = { handleSubmit } >
        <
        div >
        <
        label > Resource Type: < /label> <
        input type = "text"
        name = "resourceType"
        value = { formData.resourceType }
        onChange = { handleChange }
        /> <
        /div> <
        div >
        <
        label > Capacity(GB): < /label> <
        input type = "number"
        name = "capacity"
        value = { formData.capacity }
        onChange = { handleChange }
        /> <
        /div> <
        div >
        <
        label > vCPU: < /label> <
        input type = "number"
        name = "vCPU"
        value = { formData.vCPU }
        onChange = { handleChange }
        /> <
        /div> <
        div >
        <
        label > Price Per Hour: < /label> <
        input type = "number"
        name = "pricePerHour"
        value = { formData.pricePerHour }
        onChange = { handleChange }
        /> <
        /div> <
        button type = "submit" > Submit < /button> <
        /form> {
            estimatedCost && < p > Estimated Cost: { estimatedCost } < /p>} <
                /div>
        );
    }

    export default App;