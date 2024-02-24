import { useEffect } from "react";
import { Socket } from "socket.io-client";

interface Department {
    name: string;
    code: string;
};

type Props = {
  setDepartment: (department: Department) => void;
  socket: Socket
};

export default function SelectDepartment({socket , setDepartment}: Props) {
  
    const fetchDepartments = () => {
        
        socket.on("departments", (data: any) => {
            const regions: Set<string> = new Set(); // Utilisation d'un ensemble pour stocker uniquement des valeurs uniques

            data.forEach((item: any) => {
                regions.add(item.region_name);
              });

            console.log(regions)
        });

        socket.emit("get_departments");

    }

    useEffect(() => {
        fetchDepartments();
    }, [])
    

    return (
    <div>
      <div>Select your Department</div>
    </div>
  );
}
