import { BrowserRouter, Routes, Route } from "react-router"
import { Login } from "../pages/Login"
import type { FC } from "react"
import { routes } from "./routes"

export const Router: FC = () => {
    return (
        <BrowserRouter>
            <Routes>
                <Route path={routes.LOGIN} element={<Login />} />
            </Routes>
        </BrowserRouter>
    )
}