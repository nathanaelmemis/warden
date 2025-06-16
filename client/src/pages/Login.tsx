import { Box, Button, Divider, Link, Stack, Typography } from "@mui/material";
import { useForm, type SubmitHandler } from "react-hook-form"

import { Background } from "../components/Background";
import { type FC } from "react";
import { ValidationTextField } from "../components/ValidationTextField";

type Inputs = {
    email: string
    password: string
}

export const Login: FC = () => {
    const {
        register,
        handleSubmit,
        formState: { errors },
    } = useForm<Inputs>()

    const onSubmit: SubmitHandler<Inputs> = (data) => {
        
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
                onSubmit={handleSubmit(onSubmit)}
            >
                <Typography
                    variant="h3" fontWeight="bold">Warden</Typography>
                <ValidationTextField
                    name="email"
                    label="Email"
                    register={register}
                    rules={{
                        required: 'Email is required',
                        pattern: {
                            value: /^[a-zA-Z0-9]([a-zA-Z0-9]){1,}((\.|-|\+|_)([a-zA-Z0-9]){2,})*@g(oogle)?mail\.com$/,
                            message: "Invalid email format"
                        }
                    }}
                    error={errors.email}
                />
                <ValidationTextField
                    name="password"
                    label="Password"
                    type="password"
                    register={register}
                    rules={{
                        required: 'Password is required',
                    }}
                    error={errors.password}
                />
                <Box
                    display="flex"
                    justifyContent="right"
                >
                    <Button fullWidth variant="contained" type="submit">Login</Button>
                </Box>
                <Box
                    display="flex"
                    justifyContent="center"
                >
                    <Typography textAlign="center" mr=".5em">New User?</Typography>
                    <Link href="/register" underline="none">Sign Up</Link>
                </Box>
            </Stack>
        </Background>
    )
}