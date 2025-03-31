console.log("js calling")

function bench_migrate(){
    console.log("bench_command calling")
    fetch('/api/method/sarvadhi_custom.www.bench_command.bench.bench_migrate',{
    })
    .then(response=>{
        if(response.ok){
            console.log("bench migrate successfully")
        }
        else{
            console.log("bench migrate not valid")
        }
    }
    )
}

function bench_build(){
    console.log("bench_command calling")
    fetch('/api/method/sarvadhi_custom.www.bench_command.bench.bench_build',{
        method: 'GET',
    })
    .then(response=>{
        if(response.ok){
            console.log("bench migrate successfully")
        }
        else{
            console.log("bench migrate not valid")
        }
    }
    )
}

function bench_clear_cache(){
    console.log("bench_command calling")
    fetch('/api/method/sarvadhi_custom.www.bench_command.bench.bench_clear_cache',{
        method: 'GET',
    })
    .then(response=>{
        if(response.ok){
            console.log("bench migrate successfully")
        }
        else{
            console.log("bench migrate not valid")
        }
    }
    )
}




function bench_site(){
    console.log("bench_site calling")
    console.log("name:",name)
    console.log("root_pwd:",root)
    console.log("site_pwd:",site_pwd)
    console.log("re_site_pwd:",re_site_pwd)

    formdata={
        site_name:document.getElementById('name').value,
        root_pwd:document.getElementById('root').value,
        site_pwd:document.getElementById('site_pwd').value,
        re_site_pwd:document.getElementById('re_site_pwd').value,
    }
    
   console.log("formadata:",formdata)
   url='/api/method/sarvadhi_custom.www.bench_command.bench.bench_site'
    fetch(url,{
        method: 'POST',
        headers: { 
            // 'Authorization': 'token 1b99bc035156c5d:e97ea4de450d04a',
            'Content-Type': 'application/json' 
        },
        body: JSON.stringify(formdata)
    })
    .then(response => response.json())
    .then(data => {
              
        console.log("data:",data);
        if (data.exc) {
            console.error("Error:", data.exc);
        }
       
    })
    .catch(error => console.error("Request failed:", error));

}




function uploadResume() {
    const file = document.getElementById('resume').files[0];
    // docname=document.getElementById('docname').value;
    docname='091'
    // doctype=document.getElementById('doctype').value;
    doctype='custom_doc'
    console.log("docname:",docname)
    console.log("doctype:",doctype)

    url='/api/method/sarvadhi_custom.www.bench_command.bench.attach_resume'

    if (!file) {
        alert("Please select a file");
        return;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('doctype', doctype);
    formData.append('docname', docname);

    fetch(url, {
        method: 'POST',
       
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            alert("Resume uploaded successfully!");
            console.log("Uploaded File:", data.message);
        } else {
            alert("Failed to upload resume.");
        }
    })
    .catch(error => console.error('Error:', error));
}
