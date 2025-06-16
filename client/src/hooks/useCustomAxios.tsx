import axios from "axios"
import { useNavigate } from "react-router-dom"
import { routes } from "../router/routes"

export const useCustomAxios = () => {
    const navigate = useNavigate()

    const customAxios = axios.create({
        withCredentials: true
    })

    customAxios.interceptors.response.use(
        response => response,
        async error => {
            try {
                // invalid tokens
                if (error.status === 401) {
                    await axios.post("/api/admin/logout")
                    navigate(routes.LOGIN)
                }

                const originalRequest = error.config

                // expired access token, try to fetch new access token using refresh token then redo request
                if (error.status === 403 && !originalRequest._retry) {
                    originalRequest._retry = true;

                    await axios.get("/api/admin/refresh")

                    return await axios(originalRequest)
                }
            } catch (error: any) {
                // invalid refresh token
                if (error.status === 401) {
                    await axios.post("/api/admin/logout")
                    navigate(routes.LOGIN)
                }
            }
        }
    )

    return customAxios
}