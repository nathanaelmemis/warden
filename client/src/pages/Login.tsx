import { Box, Button, Stack, TextField, Typography } from "@mui/material";
import { Background } from "../components/Background";
import { useState, type ChangeEvent, type FC } from "react";

export const Login: FC = () => {
    const [email, setEmail] = useState("")
    const [password, setPassword] = useState("")

    const handleEmailTextFieldChange = (event: ChangeEvent<HTMLInputElement>) => {
        setEmail(event.target.value)
    }

    const handlePasswordTextFieldChange = (event: ChangeEvent<HTMLInputElement>) => {
        setPassword(event.target.value)
    }

    const handleSubmit = () => {
        console.log(email, password)
    }

    return (
        <Background
            display="flex"
            justifyContent="center"
            alignItems="center"
        >
            <Stack
                padding={4}
                spacing={2}
                borderRadius={2}
                width="20em"
                sx={{
                    backgroundColor: "secondary.main"
                }}
                component="form"
                onSubmit={handleSubmit}
            >
                <Typography 
                    variant="h3" fontWeight="bold">Warden</Typography>
                <TextField
                    label="Email"
                    value={email}
                    onChange={handleEmailTextFieldChange}
                />
                <TextField
                    label="Password"
                    value={password}
                    onChange={handlePasswordTextFieldChange}
                />
                <Box
                    display="flex"
                    justifyContent="right"
                >
                    <Button variant="contained" type="submit">Login</Button>
                </Box>
            </Stack>
        </Background>
    )
}