import { BrowserRouter, Routes, Route } from "react-router"
import { Login } from "../pages/Login"
import type { FC } from "react"

export const Router: FC = () => {
    return (
        <BrowserRouter>
            <Routes>
                <Route path="/login" element={<Login />} />
            </Routes>
        </BrowserRouter>
    )
}