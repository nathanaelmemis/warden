import { useEffect, useState, type FC } from "react";
import { Background } from "../components/Background";
import { useCustomAxios } from "../hooks/useCustomAxios";
import type { App } from "../types/App";
import { Box, Button, IconButton, Stack, Typography } from "@mui/material";
import EditIcon from '@mui/icons-material/Edit';
import AddIcon from '@mui/icons-material/Add';
import AccountCircleIcon from '@mui/icons-material/AccountCircle';

export const Dashboard: FC = () => {
    const customAxios = useCustomAxios()
    const [apps, setApps] = useState<App[]>([])

    useEffect(() => {
        customAxios.get("/api/admin/app").then((response) => {
            console.log(response.data)
            // const dummyData = [
            //     ...response.data,
            //     ...response.data,
            //     ...response.data,
            //     ...response.data,
            //     ...response.data,
            //     ...response.data,
            //     ...response.data,
            //     ...response.data,
            //     ...response.data,
            //     ...response.data,
            //     ...response.data,
            //     ...response.data,
            //     ...response.data,
            //     ...response.data,
            //     ...response.data,
            //     ...response.data,
            //     ...response.data,
            // ]
            // setApps(dummyData)
            setApps(response.data)
        })
    }, [])

    return (
        <Background
            display="flex"
            justifyContent="center"
            alignItems="center"
            flexDirection='column'
        >
            <Box
                display='flex'
                justifyContent='flex-end'
                width='34em'
            >
                <IconButton
                    color="secondary"
                >
                    <AccountCircleIcon fontSize='large' />
                </IconButton>
            </Box>
            <Stack
                padding={4}
                spacing={2}
                borderRadius={2}
                width="30em"
                height="40em"
                sx={{
                    backgroundColor: "secondary.main"
                }}
            >
                <Typography
                    variant="h4"
                    fontWeight="bold"
                    textAlign='center'
                >
                    Apps
                </Typography>
                <Stack
                    overflow='auto'
                    spacing={1}
                    p={2}
                    sx={(theme) => ({
                        /* width */
                        '::-webkit-scrollbar': {
                            width: '10px'
                        },
                        /* Track */
                        '::-webkit-scrollbar-track': {
                            background: theme.palette.secondary.light,
                            borderRadius: 25
                        },
                        /* Handle */
                        '::-webkit-scrollbar-thumb': {
                            background: theme.palette.primary.main,
                            borderRadius: 25
                        },
                    })}
                >
                    {
                        apps.map((app) => (
                            <Box
                                alignItems='center'
                                border='1px solid black'
                                p={2}
                                borderRadius={2}
                                bgcolor='secondary.main'
                                sx={(theme) => ({
                                    cursor: 'pointer',
                                    animation: 'all 1s ease',
                                    '&:hover': {
                                        backgroundColor: theme.palette.secondary.dark
                                    }
                                })}
                            >
                                <Typography>
                                    {app.name}
                                </Typography>
                            </Box>
                        ))
                    }
                </Stack>
                <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                >
                    Create App
                </Button>
            </Stack>
        </Background>
    )
}