import { BrowserRouter, Routes, Route } from "react-router"
import { Login } from "../pages/Login"
import type { FC } from "react"
import { routes } from "./routes"
import { Dashboard } from "../pages/Dashboard"

export const Router: FC = () => {
    return (
        <BrowserRouter>
            <Routes>
                <Route path={routes.LOGIN} element={<Login />} />
                <Route path={routes.DASHBOARD} element={<Dashboard />} />
            </Routes>
        </BrowserRouter>
    )
}