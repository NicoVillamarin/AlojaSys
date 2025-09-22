import { Outlet } from "react-router-dom";
import Sidebar from "src/components/Sidebar";
import Navbar from "src/components/Navbar";

export default function MainLayout() {

  return (
    <div className="min-h-screen w-full flex bg-aloja-gray-50">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        <Navbar />
        <main className="flex-1 p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}


